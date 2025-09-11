#!/bin/bash
# Скрипт настройки конфигурации (.env файл) для Mind Style Bot

set -e  # Остановка при ошибках

PROJECT_DIR="/opt/mind_style_bot"

echo "⚙️ Настройка конфигурации Mind Style Bot..."

# Запрос токена бота у пользователя
echo "🤖 Введите токен Telegram бота (получить можно у @BotFather):"
read -r BOT_TOKEN

# Запрос ID администратора
echo "👤 Введите Telegram ID администратора (ваш ID):"
read -r ADMIN_USER_ID

# Запрос домена для webhook
echo "🌐 Введите домен для webhook (например: example.com):"
read -r WEBHOOK_DOMAIN

# Загрузка параметров БД из сохраненного файла
source $PROJECT_DIR/.db_credentials

# Создание .env файла для production
echo "📝 Создание .env файла..."
sudo -u mind_style_bot bash -c "cat > $PROJECT_DIR/.env <<EOF
# Telegram Bot Configuration
BOT_TOKEN=$BOT_TOKEN
ADMIN_USER_ID=$ADMIN_USER_ID

# Database Configuration
DATABASE_URL=$DATABASE_URL

# Environment Configuration
DEBUG=False

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Webhook Configuration
WEBHOOK_URL=https://$WEBHOOK_DOMAIN/webhook

# Senler Integration (optional)
SENLER_TOKEN=
SENLER_USER_ID=
EOF"

# Создание backup существующего .env если он есть
if [ -f "$PROJECT_DIR/.env.backup" ]; then
    echo "💾 Создание резервной копии существующего .env..."
    sudo -u mind_style_bot cp $PROJECT_DIR/.env $PROJECT_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)
fi

# Установка прав на .env файл
sudo chmod 600 $PROJECT_DIR/.env

# Проверка конфигурации
echo "✅ Проверка созданного .env файла..."
sudo -u mind_style_bot head -5 $PROJECT_DIR/.env

echo "✅ Конфигурация настроена успешно!"
echo "📁 Файл конфигурации: $PROJECT_DIR/.env"
echo "🔐 Права доступа установлены (600)"
echo ""
echo "🔧 Следующие шаги:"
echo "   1. Проверьте настройки в .env файле"
echo "   2. При необходимости добавьте Senler токены"
echo "   3. Настройте SSL сертификат для домена $WEBHOOK_DOMAIN"