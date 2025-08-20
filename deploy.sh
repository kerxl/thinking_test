#!/bin/bash
# Автоматический скрипт деплоя Mind Style Bot

set -e

echo "🚀 Начинаем деплой Mind Style Bot..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Проверка запуска от имени root
if [ "$EUID" -eq 0 ]; then
    error "Не запускайте этот скрипт от имени root!"
fi

# Проверка наличия необходимых переменных
if [ -z "$BOT_TOKEN" ]; then
    warn "BOT_TOKEN не установлен. Вы можете установить его после деплоя в .env файле"
fi

if [ -z "$DOMAIN" ]; then
    read -p "Введите домен для деплоя (например, bot.example.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        error "Домен обязателен для настройки SSL и webhook"
    fi
fi

if [ -z "$DB_PASSWORD" ]; then
    read -s -p "Введите пароль для базы данных PostgreSQL: " DB_PASSWORD
    echo
    if [ -z "$DB_PASSWORD" ]; then
        error "Пароль для БД обязателен"
    fi
fi

log "Конфигурация:"
log "  Домен: $DOMAIN"
log "  Пользователь: $(whoami)"
log "  Директория: $(pwd)"

# Проверка системных требований
log "Проверка системных требований..."

if ! command -v python3 &> /dev/null; then
    error "Python 3 не установлен"
fi

if ! command -v git &> /dev/null; then
    error "Git не установлен"
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    error "Требуется Python 3.8 или выше, установлен: $PYTHON_VERSION"
fi

log "✅ Системные требования выполнены"

# Создание виртуального окружения
log "Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log "✅ Виртуальное окружение создано"
else
    log "ℹ️  Виртуальное окружение уже существует"
fi

# Активация и установка зависимостей
log "Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
log "✅ Зависимости установлены"

# Создание .env файла
log "Настройка переменных окружения..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=${BOT_TOKEN:-your_bot_token_here}

# База данных
DATABASE_URL=postgresql+asyncpg://mindbot:${DB_PASSWORD}@localhost/mind_style

# Общие настройки
DEBUG=False
ADMIN_USER_ID=${ADMIN_USER_ID:-0}

# API сервер для Senler
API_HOST=0.0.0.0
API_PORT=8000
WEBHOOK_URL=https://${DOMAIN}/senler/webhook
EOF
    chmod 600 .env
    log "✅ Файл .env создан"
else
    log "ℹ️  Файл .env уже существует, обновляем WEBHOOK_URL..."
    sed -i "s|WEBHOOK_URL=.*|WEBHOOK_URL=https://${DOMAIN}/senler/webhook|g" .env
fi

# Проверка подключения к PostgreSQL
log "Проверка подключения к PostgreSQL..."
if sudo -u postgres psql -c '\q' 2>/dev/null; then
    log "✅ PostgreSQL доступен"
else
    error "PostgreSQL недоступен. Убедитесь, что он установлен и запущен."
fi

# Создание БД и пользователя
log "Настройка базы данных..."
sudo -u postgres psql -c "CREATE DATABASE mind_style;" 2>/dev/null || log "ℹ️  База данных mind_style уже существует"
sudo -u postgres psql -c "CREATE USER mindbot WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || log "ℹ️  Пользователь mindbot уже существует"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mind_style TO mindbot;" 2>/dev/null

# Инициализация БД
log "Инициализация базы данных..."
make db-init
make db-senler
log "✅ База данных настроена"

# Создание systemd сервиса
log "Создание systemd сервиса..."
sudo tee /etc/systemd/system/mindbot-api.service > /dev/null << EOF
[Unit]
Description=Mind Style Bot with API
After=network.target postgresql.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python src/run_with_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mindbot-api
log "✅ Systemd сервис создан"

# Создание конфигурации Nginx
log "Создание конфигурации Nginx..."
sudo tee /etc/nginx/sites-available/mindbot > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL сертификаты будут настроены автоматически через certbot
    
    # Proxy для API сервера
    location /senler/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # API docs (optional)
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # Основная страница
    location / {
        return 200 'Mind Style Bot API is running';
        add_header Content-Type text/plain;
    }
}
EOF

# Активация сайта в Nginx
sudo ln -sf /etc/nginx/sites-available/mindbot /etc/nginx/sites-enabled/
sudo nginx -t
log "✅ Конфигурация Nginx создана"

# Получение SSL сертификата
log "Получение SSL сертификата..."
if command -v certbot &> /dev/null; then
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    log "✅ SSL сертификат получен"
else
    warn "Certbot не установлен. Установите SSL сертификат вручную."
fi

# Перезапуск служб
log "Перезапуск служб..."
sudo systemctl restart nginx
sudo systemctl start mindbot-api
log "✅ Службы запущены"

# Проверка статуса
log "Проверка статуса деплоя..."
sleep 5

if sudo systemctl is-active --quiet mindbot-api; then
    log "✅ Mind Style Bot API запущен"
else
    error "❌ Mind Style Bot API не запущен. Проверьте логи: sudo journalctl -u mindbot-api"
fi

if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx работает"
else
    error "❌ Nginx не работает"
fi

# Финальная проверка
log "Финальная проверка..."
if curl -f https://$DOMAIN/health &> /dev/null; then
    log "✅ API отвечает по HTTPS"
elif curl -f http://$DOMAIN:8000/health &> /dev/null; then
    warn "⚠️  API работает, но SSL может быть не настроен"
else
    warn "⚠️  API не отвечает. Проверьте конфигурацию."
fi

# Создание скриптов управления
log "Создание скриптов управления..."

# Скрипт для проверки статуса
cat > check_status.sh << 'EOF'
#!/bin/bash
echo "=== Mind Style Bot Status ==="
echo "Service status:"
sudo systemctl status mindbot-api --no-pager -l
echo -e "\nAPI Health:"
curl -s https://$(grep WEBHOOK_URL .env | cut -d'=' -f2 | cut -d'/' -f3)/health | jq . || echo "API not responding"
echo -e "\nLast 10 log entries:"
sudo journalctl -u mindbot-api -n 10 --no-pager
EOF

# Скрипт для обновления
cat > update_bot.sh << 'EOF'
#!/bin/bash
echo "Updating Mind Style Bot..."
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mindbot-api
echo "Bot updated successfully!"
echo "Status:"
sleep 2
sudo systemctl status mindbot-api --no-pager -l
EOF

# Скрипт для просмотра логов
cat > view_logs.sh << 'EOF'
#!/bin/bash
echo "Mind Style Bot Logs (press Ctrl+C to exit):"
sudo journalctl -u mindbot-api -f
EOF

chmod +x check_status.sh update_bot.sh view_logs.sh

log "✅ Скрипты управления созданы:"
log "  ./check_status.sh - проверка статуса"
log "  ./update_bot.sh   - обновление бота"
log "  ./view_logs.sh    - просмотр логов"

# Итоговая информация
echo
echo "🎉 Деплой завершен успешно!"
echo
echo "📋 Информация о деплое:"
echo "  Домен: https://$DOMAIN"
echo "  Webhook URL: https://$DOMAIN/senler/webhook"
echo "  Health Check: https://$DOMAIN/health"
echo "  API Docs: https://$DOMAIN/docs"
echo
echo "🔧 Что делать дальше:"
echo "  1. Обновите BOT_TOKEN в файле .env"
echo "  2. Перезапустите сервис: sudo systemctl restart mindbot-api"
echo "  3. Настройте Senler воронку с webhook URL выше"
echo "  4. Протестируйте интеграцию"
echo
echo "📊 Полезные команды:"
echo "  Статус:    ./check_status.sh"
echo "  Логи:      ./view_logs.sh"
echo "  Обновить:  ./update_bot.sh"
echo "  Рестарт:   sudo systemctl restart mindbot-api"
echo
echo "📚 Документация:"
echo "  Полная инструкция: DEPLOYMENT_GUIDE.md"
echo "  Senler интеграция: SENLER_INTEGRATION.md"

log "🚀 Mind Style Bot готов к работе!"