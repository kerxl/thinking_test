#!/bin/bash
# Скрипт установки системных зависимостей для Mind Style Bot

set -e  # Остановка при ошибках

echo "🚀 Установка системных зависимостей для Mind Style Bot..."

# Обновление списка пакетов
echo "📦 Обновление списка пакетов..."
sudo apt update

# Установка основных системных зависимостей
echo "🛠️ Установка системных пакетов..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    mysql-server \
    mysql-client \
    nginx \
    git \
    curl \
    wget \
    unzip \
    supervisor \
    htop \
    nano \
    vim

# Установка дополнительных пакетов для Python
echo "🐍 Установка дополнительных Python зависимостей..."
sudo apt install -y \
    python3-dev \
    libmysqlclient-dev \
    build-essential \
    pkg-config

# Проверка установки Python
echo "✅ Проверка версии Python..."
python3 --version
pip3 --version

# Проверка установки MySQL
echo "🗄️ Проверка установки MySQL..."
mysql --version

# Проверка установки Nginx
echo "🌐 Проверка установки Nginx..."
nginx -v

echo "✅ Все системные зависимости установлены успешно!"