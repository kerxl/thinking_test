# 🚀 Руководство по деплою Mind Style Bot

Полное руководство по развертыванию Mind Style Bot на сервере заказчика в режиме webhook.

## 📋 Требования к серверу

### Операционная система
- Ubuntu 20.04+ или Debian 11+
- Права sudo для пользователя

### Системные требования
- RAM: минимум 1GB (рекомендуется 2GB+)
- Дисковое пространство: минимум 2GB
- Открытые порты: 80, 443, 8000

### Домен
- Зарегистрированный домен
- DNS записи настроены на IP сервера
- Возможность получения SSL сертификата (Let's Encrypt)

## 🛠️ Быстрый деплой

### 1. Подготовка
```bash
# Клонирование проекта
git clone <repository_url>
cd mind-style-bot

# Установка прав на выполнение
chmod +x deploy.sh
```

### 2. Запуск деплоя
```bash
./deploy.sh
```

Скрипт выполнит:
- ✅ Проверку системы
- ✅ Установку зависимостей (Python, MySQL, Nginx)
- ✅ Создание пользователя `mind_style_bot`
- ✅ Настройку базы данных MySQL
- ✅ Настройку Python окружения
- ✅ Создание systemd сервиса
- ✅ Настройку Nginx
- ✅ Запуск бота

### 3. Настройка SSL
```bash
# После деплоя выполните:
setup-ssl-mind-style-bot
```

## 📁 Структура после деплоя

```
/opt/mind_style_bot/           # Основная директория проекта
├── src/                       # Исходный код
├── venv/                      # Виртуальное окружение Python
├── .env                       # Конфигурация (секретная)
├── .db_credentials           # Параметры БД (секретная)
└── requirements.txt          # Зависимости Python

/etc/systemd/system/
└── mind-style-bot.service    # Systemd сервис

/etc/nginx/sites-available/
└── mind-style-bot           # Конфигурация Nginx

/var/log/mind_style_bot/     # Логи приложения
/usr/local/bin/
├── mind-style-bot           # Скрипт управления
└── setup-ssl-mind-style-bot # Установка SSL
```

## 🎛️ Управление ботом

### Основные команды
```bash
mind-style-bot start         # Запустить бота
mind-style-bot stop          # Остановить бота  
mind-style-bot restart       # Перезапустить бота
mind-style-bot status        # Показать статус
mind-style-bot logs          # Показать логи
mind-style-bot logs-follow   # Отслеживать логи
mind-style-bot enable        # Включить автозапуск
mind-style-bot disable       # Отключить автозапуск
mind-style-bot update-db     # Обновить схему БД
```

### Проверка работы
```bash
# Статус сервиса
sudo systemctl status mind-style-bot

# Логи в реальном времени
sudo journalctl -u mind-style-bot -f

# Проверка API
curl https://yourdomain.com/health
```

## ⚙️ Конфигурация

### Файл .env
Основные параметры в `/opt/mind_style_bot/.env`:

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token

# База данных (автогенерируется)
DATABASE_URL=mysql+aiomysql://mind_style_bot:password@localhost/mind_style_bot

# Администратор
ADMIN_USER_ID=your_telegram_id

# Webhook
WEBHOOK_URL=https://yourdomain.com/webhook

# Режим
DEBUG=False
```

### Изменение конфигурации
```bash
# Редактирование .env
sudo nano /opt/mind_style_bot/.env

# Перезапуск после изменений
mind-style-bot restart
```

## 🌐 Настройка webhook

### URL для Telegram Bot
```
https://yourdomain.com/webhook
```

### URL для Senler
```
https://yourdomain.com/senler/webhook
```

### Проверка здоровья
```
https://yourdomain.com/health
```

## 🔧 Устранение проблем

### Проблемы с запуском
```bash
# Проверка логов
mind-style-bot logs

# Статус сервиса
mind-style-bot status

# Проверка конфигурации
sudo -u mind_style_bot cat /opt/mind_style_bot/.env
```

### Проблемы с базой данных
```bash
# Проверка подключения MySQL
sudo mysql -u mind_style_bot -p mind_style_bot

# Обновление схемы БД
mind-style-bot update-db

# Пересоздание БД (ОСТОРОЖНО!)
sudo mysql -u root -p -e "DROP DATABASE mind_style_bot; CREATE DATABASE mind_style_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Проблемы с SSL
```bash
# Проверка сертификата
sudo certbot certificates

# Обновление сертификата
sudo certbot renew --dry-run

# Переустановка SSL
setup-ssl-mind-style-bot
```

### Проблемы с Nginx
```bash
# Проверка конфигурации
sudo nginx -t

# Перезагрузка Nginx
sudo systemctl reload nginx

# Логи Nginx
sudo tail -f /var/log/nginx/mind-style-bot-error.log
```

## 🔄 Обновление бота

### Обновление кода
```bash
cd /opt/mind_style_bot
sudo -u mind_style_bot git pull
sudo -u mind_style_bot bash -c "source venv/bin/activate && pip install -r requirements.txt"
mind-style-bot restart
```

### Обновление зависимостей
```bash
cd /opt/mind_style_bot
sudo -u mind_style_bot bash -c "source venv/bin/activate && pip install --upgrade -r requirements.txt"
mind-style-bot restart
```

## 💾 Резервное копирование

### База данных
```bash
# Создание бэкапа
mysqldump -u mind_style_bot -p mind_style_bot > backup_$(date +%Y%m%d).sql

# Восстановление
mysql -u mind_style_bot -p mind_style_bot < backup_20240808.sql
```

### Конфигурация
```bash
# Бэкап конфигурации
sudo cp /opt/mind_style_bot/.env /opt/mind_style_bot/.env.backup.$(date +%Y%m%d)
```

## 📊 Мониторинг

### Системный мониторинг
```bash
# Использование ресурсов
htop

# Место на диске
df -h

# Статус MySQL
sudo systemctl status mysql

# Статус Nginx  
sudo systemctl status nginx
```

### Мониторинг приложения
```bash
# Активные соединения
ss -tuln | grep :8000

# Логи ошибок
sudo journalctl -u mind-style-bot --since "1 hour ago" -p err

# Здоровье API
watch curl -s https://yourdomain.com/health
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте статус всех сервисов
2. Изучите логи: `mind-style-bot logs`
3. Убедитесь, что порты 80, 443, 8000 открыты
4. Проверьте DNS записи домена
5. Убедитесь, что SSL сертификат действителен

## 📝 Дополнительные файлы

- `CLAUDE.md` - инструкции для разработки
- `SENLER_INTEGRATION.md` - интеграция с Senler
- `requirements.txt` - Python зависимости
- `alembic/` - миграции базы данных

---

🤖 Mind Style Bot готов к работе в production среде!