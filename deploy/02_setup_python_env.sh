#!/bin/bash
# Скрипт настройки Python окружения для Mind Style Bot

set -e  # Остановка при ошибках

PROJECT_DIR="/opt/mind_style_bot"
SERVICE_USER="mind_style_bot"

echo "🐍 Настройка Python окружения для Mind Style Bot..."

# Создание пользователя для сервиса (если не существует)
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "👤 Создание пользователя $SERVICE_USER..."
    sudo useradd --system --shell /bin/bash --home-dir $PROJECT_DIR $SERVICE_USER
fi

# Создание директории проекта
echo "📁 Создание директории проекта..."
sudo mkdir -p $PROJECT_DIR
sudo chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# Копирование проекта в целевую директорию
echo "📋 Копирование файлов проекта..."
sudo -u $SERVICE_USER cp -r . $PROJECT_DIR/
cd $PROJECT_DIR

# Создание виртуального окружения
echo "🏗️ Создание виртуального окружения..."
sudo -u $SERVICE_USER python3 -m venv venv

# Активация виртуального окружения и установка зависимостей
echo "📦 Установка Python зависимостей..."
sudo -u $SERVICE_USER bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"

# Создание директорий для логов
echo "📝 Создание директорий для логов..."
sudo mkdir -p /var/log/mind_style_bot
sudo chown $SERVICE_USER:$SERVICE_USER /var/log/mind_style_bot

# Установка прав доступа
echo "🔐 Настройка прав доступа..."
sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
sudo chmod +x $PROJECT_DIR/src/run_webhook_mode.py

echo "✅ Python окружение настроено успешно!"
echo "📍 Проект размещен в: $PROJECT_DIR"
echo "👤 Пользователь сервиса: $SERVICE_USER"