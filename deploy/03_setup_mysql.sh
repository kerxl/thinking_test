#!/bin/bash
# Скрипт настройки базы данных MySQL для Mind Style Bot

set -e  # Остановка при ошибках

DB_NAME="mind_style_bot"
DB_USER="mind_style_bot"
PROJECT_DIR="/opt/mind_style_bot"

echo "🗄️ Настройка базы данных MySQL для Mind Style Bot..."

# Генерация случайного пароля для БД
DB_PASSWORD=$(openssl rand -base64 32)

echo "🔒 Сгенерированный пароль для БД: $DB_PASSWORD"

# Настройка безопасности MySQL
echo "🔐 Настройка безопасности MySQL..."
sudo mysql_secure_installation <<EOF

y
$DB_PASSWORD
$DB_PASSWORD
y
y
y
y
EOF

# Создание базы данных и пользователя
echo "📊 Создание базы данных и пользователя..."
sudo mysql -u root -p$DB_PASSWORD <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# Запуск и включение MySQL в автозагрузку
echo "🚀 Включение MySQL в автозагрузку..."
sudo systemctl enable mysql
sudo systemctl start mysql

# Проверка статуса MySQL
echo "✅ Проверка статуса MySQL..."
sudo systemctl status mysql --no-pager -l

# Сохранение параметров БД в файл для дальнейшего использования
echo "💾 Сохранение параметров БД..."
sudo -u mind_style_bot bash -c "cat > $PROJECT_DIR/.db_credentials <<EOF
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=mysql+aiomysql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
EOF"

# Установка прав на файл с учетными данными
sudo chmod 600 $PROJECT_DIR/.db_credentials

echo "✅ База данных MySQL настроена успешно!"
echo "📋 База данных: $DB_NAME"
echo "👤 Пользователь БД: $DB_USER"
echo "🔑 Пароль сохранен в: $PROJECT_DIR/.db_credentials"