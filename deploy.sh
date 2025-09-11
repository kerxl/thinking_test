#!/bin/bash
# Главный скрипт деплоя Mind Style Bot на сервер заказчика
# Этот скрипт выполнит полную установку и настройку бота в режиме webhook

set -e  # Остановка при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для цветного вывода
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Проверка прав root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "Этот скрипт НЕ должен запускаться от root!"
        print_status "Запустите скрипт от обычного пользователя с правами sudo"
        exit 1
    fi
}

# Проверка наличия sudo
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        print_error "Необходимы права sudo для выполнения установки"
        exit 1
    fi
}

# Проверка системы
check_system() {
    print_status "Проверка системы..."
    
    if ! command -v lsb_release &> /dev/null; then
        sudo apt update && sudo apt install -y lsb-release
    fi
    
    OS=$(lsb_release -si)
    VERSION=$(lsb_release -sr)
    
    print_status "Операционная система: $OS $VERSION"
    
    if [[ "$OS" != "Ubuntu" ]] && [[ "$OS" != "Debian" ]]; then
        print_warning "Скрипт протестирован только на Ubuntu/Debian"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Основная функция деплоя
main() {
    print_header "🚀 ДЕПЛОЙ MIND STYLE BOT НА СЕРВЕР ЗАКАЗЧИКА"
    
    # Проверки
    check_root
    check_sudo
    check_system
    
    print_status "Текущая директория: $(pwd)"
    print_status "Пользователь: $(whoami)"
    
    # Предупреждение
    print_warning "ВНИМАНИЕ! Этот скрипт выполнит следующие действия:"
    echo "  • Установит системные зависимости (Python, MySQL, Nginx)"
    echo "  • Создаст пользователя mind_style_bot"
    echo "  • Настроит базу данных MySQL"
    echo "  • Создаст systemd сервис для автозапуска"
    echo "  • Настроит Nginx для webhook"
    echo "  • Скопирует проект в /opt/mind_style_bot"
    echo ""
    
    read -p "Продолжить установку? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Установка отменена пользователем"
        exit 0
    fi
    
    # Создание директории deploy если не существует
    mkdir -p deploy
    
    # Делаем все скрипты исполняемыми
    chmod +x deploy/*.sh 2>/dev/null || true
    
    # Этап 1: Установка системных зависимостей
    print_header "📦 ЭТАП 1: Установка системных зависимостей"
    if [ -f "deploy/01_install_system_deps.sh" ]; then
        ./deploy/01_install_system_deps.sh
        print_success "Системные зависимости установлены"
    else
        print_error "Файл deploy/01_install_system_deps.sh не найден"
        exit 1
    fi
    
    # Этап 2: Настройка Python окружения
    print_header "🐍 ЭТАП 2: Настройка Python окружения"
    if [ -f "deploy/02_setup_python_env.sh" ]; then
        ./deploy/02_setup_python_env.sh
        print_success "Python окружение настроено"
    else
        print_error "Файл deploy/02_setup_python_env.sh не найден"
        exit 1
    fi
    
    # Этап 3: Настройка базы данных
    print_header "🗄️ ЭТАП 3: Настройка базы данных MySQL"
    if [ -f "deploy/03_setup_mysql.sh" ]; then
        ./deploy/03_setup_mysql.sh
        print_success "База данных MySQL настроена"
    else
        print_error "Файл deploy/03_setup_mysql.sh не найден"
        exit 1
    fi
    
    # Этап 4: Настройка конфигурации
    print_header "⚙️ ЭТАП 4: Настройка конфигурации"
    if [ -f "deploy/04_setup_config.sh" ]; then
        ./deploy/04_setup_config.sh
        print_success "Конфигурация настроена"
    else
        print_error "Файл deploy/04_setup_config.sh не найден"
        exit 1
    fi
    
    # Этап 5: Настройка systemd сервиса
    print_header "🔧 ЭТАП 5: Настройка systemd сервиса"
    if [ -f "deploy/05_setup_systemd.sh" ]; then
        ./deploy/05_setup_systemd.sh
        print_success "Systemd сервис настроен"
    else
        print_error "Файл deploy/05_setup_systemd.sh не найден"
        exit 1
    fi
    
    # Этап 6: Настройка Nginx
    print_header "🌐 ЭТАП 6: Настройка Nginx"
    if [ -f "deploy/06_setup_nginx.sh" ]; then
        ./deploy/06_setup_nginx.sh
        print_success "Nginx настроен"
    else
        print_error "Файл deploy/06_setup_nginx.sh не найден"
        exit 1
    fi
    
    # Запуск бота
    print_header "🚀 ЗАПУСК MIND STYLE BOT"
    print_status "Запуск Mind Style Bot в режиме webhook..."
    
    if mind-style-bot start; then
        print_success "Mind Style Bot запущен успешно!"
    else
        print_error "Ошибка запуска бота"
        print_status "Проверьте логи: mind-style-bot logs"
        exit 1
    fi
    
    # Проверка статуса
    sleep 3
    print_status "Проверка статуса бота..."
    mind-style-bot status
    
    # Финальная информация
    print_header "✅ ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!"
    
    echo -e "${GREEN}Mind Style Bot успешно развернут и запущен!${NC}"
    echo ""
    echo "📋 Информация о установке:"
    echo "  • Проект: /opt/mind_style_bot"
    echo "  • Пользователь: mind_style_bot"
    echo "  • Сервис: mind-style-bot.service"
    echo "  • Логи: /var/log/mind_style_bot"
    echo ""
    echo "🎛️ Команды управления:"
    echo "  • mind-style-bot start    - Запустить бота"
    echo "  • mind-style-bot stop     - Остановить бота"
    echo "  • mind-style-bot restart  - Перезапустить бота"
    echo "  • mind-style-bot status   - Показать статус"
    echo "  • mind-style-bot logs     - Показать логи"
    echo ""
    echo "🔧 Следующие шаги:"
    echo "  1. Настройте DNS записи для вашего домена"
    echo "  2. Установите SSL сертификат: setup-ssl-mind-style-bot"
    echo "  3. Проверьте работу webhook в Telegram"
    echo "  4. Настройте мониторинг (опционально)"
    echo ""
    print_success "Бот готов к работе!"
}

# Обработка сигналов
trap 'print_error "Установка прервана"; exit 1' INT TERM

# Запуск основной функции
main "$@"