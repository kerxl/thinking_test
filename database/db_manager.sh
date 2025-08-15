#!/bin/bash

# ============================================
# Скрипт для управления базой данных
# ============================================

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация по умолчанию
DB_NAME="mind_style"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"

# Функции для вывода
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Проверка существования PostgreSQL
check_postgres() {
    if ! command -v psql &> /dev/null; then
        print_error "PostgreSQL не установлен. Установите его командой:"
        echo "sudo apt update && sudo apt install postgresql postgresql-contrib"
        exit 1
    fi
    
    if ! sudo systemctl is-active --quiet postgresql; then
        print_warning "PostgreSQL не запущен. Запускаю..."
        sudo systemctl start postgresql
    fi
    
    print_success "PostgreSQL готов к работе"
}

# Создание базы данных и пользователя
create_database() {
    print_info "Создание базы данных и пользователя..."
    
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        print_warning "База данных $DB_NAME уже существует"
        read -p "Пересоздать? (y/N): " recreate
        if [[ $recreate =~ ^[Yy]$ ]]; then
            sudo -u postgres psql -f database/drop_database.sql
        else
            print_info "Пропускаю создание базы данных"
            return
        fi
    fi
    
    sudo -u postgres psql -f database/create_database.sql
    print_success "База данных создана"
}

# Создание таблиц
create_tables() {
    print_info "Создание таблиц..."
    
    if PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt" 2>/dev/null | grep -q "users"; then
        print_warning "Таблицы уже существуют"
        read -p "Пересоздать? (y/N): " recreate
        if [[ $recreate =~ ^[Yy]$ ]]; then
            PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "DROP TABLE IF EXISTS users CASCADE;"
        else
            print_info "Пропускаю создание таблиц"
            return
        fi
    fi
    
    PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/create_tables.sql
    print_success "Таблицы созданы"
}

# Получение пароля базы данных из .env
get_db_password() {
    if [ -f .env ]; then
        grep "DATABASE_URL=" .env | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/'
    else
        print_error "Файл .env не найден"
        exit 1
    fi
}

# Очистка данных
clean_data() {
    print_warning "Это действие удалит ВСЕ данные из базы данных!"
    read -p "Продолжить? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/clean_database.sql
        print_success "Данные очищены"
    else
        print_info "Операция отменена"
    fi
}

# Вставка тестовых данных
insert_sample_data() {
    print_info "Вставка тестовых данных..."
    PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/sample_data.sql
    print_success "Тестовые данные добавлены"
}

# Проверка подключения
test_connection() {
    print_info "Проверка подключения к базе данных..."
    
    if PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "Подключение к базе данных успешно"
        
        # Показать статистику
        PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        SELECT 
            'Пользователей всего: ' || COUNT(*) || 
            ', завершили тест: ' || COUNT(*) FILTER (WHERE test_completed = TRUE) ||
            ', в процессе: ' || COUNT(*) FILTER (WHERE test_completed = FALSE) as stats
        FROM users;
        "
    else
        print_error "Не удается подключиться к базе данных"
        return 1
    fi
}

# Бэкап базы данных
backup_database() {
    print_info "Создание бэкапа базы данных..."
    
    backup_dir="backups"
    mkdir -p $backup_dir
    
    backup_file="$backup_dir/${DB_NAME}_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    PGPASSWORD=$(get_db_password) pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME > $backup_file
    
    print_success "Бэкап создан: $backup_file"
}

# Восстановление из бэкапа
restore_database() {
    print_info "Восстановление из бэкапа..."
    
    backup_dir="backups"
    if [ ! -d "$backup_dir" ] || [ -z "$(ls -A $backup_dir 2>/dev/null)" ]; then
        print_error "Папка с бэкапами пуста или не существует"
        return 1
    fi
    
    echo "Доступные бэкапы:"
    ls -la $backup_dir/*.sql 2>/dev/null | nl -v0
    
    read -p "Введите номер бэкапа для восстановления: " backup_num
    backup_file=$(ls $backup_dir/*.sql 2>/dev/null | sed -n "$((backup_num + 1))p")
    
    if [ ! -f "$backup_file" ]; then
        print_error "Файл бэкапа не найден"
        return 1
    fi
    
    print_warning "Это действие перезапишет текущие данные!"
    read -p "Продолжить? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $backup_file
        print_success "База данных восстановлена из $backup_file"
    fi
}

# Полное удаление базы данных
drop_database() {
    print_warning "Это действие ПОЛНОСТЬЮ удалит базу данных $DB_NAME!"
    read -p "Введите название базы данных для подтверждения: " confirm_name
    
    if [ "$confirm_name" = "$DB_NAME" ]; then
        sudo -u postgres psql -f database/drop_database.sql
        print_success "База данных удалена"
    else
        print_error "Название не совпадает. Операция отменена"
    fi
}

# Показать статистику
show_stats() {
    print_info "Статистика базы данных:"
    PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/queries.sql
}

# Интерактивное подключение к базе данных
connect_interactive() {
    print_info "Подключение к базе данных в интерактивном режиме..."
    print_info "Для выхода введите: \\q"
    PGPASSWORD=$(get_db_password) psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
}

# Показать справку
show_help() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Доступные команды:"
    echo "  setup          - Полная настройка (создание БД + таблицы + тестовые данные)"
    echo "  create-db      - Создать базу данных и пользователя"
    echo "  create-tables  - Создать таблицы"
    echo "  clean          - Очистить все данные"
    echo "  sample-data    - Вставить тестовые данные"
    echo "  test           - Проверить подключение"
    echo "  backup         - Создать бэкап"
    echo "  restore        - Восстановить из бэкапа"
    echo "  drop           - Удалить базу данных (ОСТОРОЖНО!)"
    echo "  stats          - Показать статистику"
    echo "  connect        - Подключиться интерактивно"
    echo "  help           - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 setup       # Полная настройка с нуля"
    echo "  $0 test        # Проверить подключение"
    echo "  $0 clean       # Очистить данные"
    echo "  $0 backup      # Создать бэкап"
}

# Основная логика
main() {
    case "${1:-help}" in
        "setup")
            check_postgres
            create_database
            create_tables
            insert_sample_data
            test_connection
            print_success "Полная настройка завершена!"
            ;;
        "create-db")
            check_postgres
            create_database
            ;;
        "create-tables")
            create_tables
            ;;
        "clean")
            clean_data
            ;;
        "sample-data")
            insert_sample_data
            ;;
        "test")
            test_connection
            ;;
        "backup")
            backup_database
            ;;
        "restore")
            restore_database
            ;;
        "drop")
            drop_database
            ;;
        "stats")
            show_stats
            ;;
        "connect")
            connect_interactive
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Проверка что запускаем из правильной директории
if [ ! -f "database/create_database.sql" ]; then
    print_error "Запустите скрипт из корневой директории проекта (06.08/)"
    exit 1
fi

main "$@"