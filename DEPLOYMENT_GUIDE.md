# 🚀 Инструкция по деплою Mind Style Bot с Senler интеграцией

## Обзор

Этот документ содержит пошаговые инструкции по:
1. Деплою бота на сервер
2. Настройке базы данных PostgreSQL
3. Настройке Senler воронки с тестовой логикой
4. Тестированию интеграции

## Часть 1: Деплой на сервер

### Предварительные требования

**На сервере должны быть установлены:**
- Ubuntu 20.04+ / CentOS 8+
- Python 3.9+
- PostgreSQL 13+
- Nginx (для проксирования)
- Git
- SSL сертификат (Let's Encrypt)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl

# Установка certbot для SSL
sudo apt install -y certbot python3-certbot-nginx
```

### Шаг 2: Настройка PostgreSQL

```bash
# Переключение на пользователя postgres
sudo -u postgres psql

-- В консоли PostgreSQL:
CREATE DATABASE mind_style;
CREATE USER mindbot WITH PASSWORD 'your_secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE mind_style TO mindbot;
\q

# Настройка доступа (редактируем pg_hba.conf)
sudo nano /etc/postgresql/13/main/pg_hba.conf
# Добавить строку:
# local   mind_style    mindbot                                md5

# Перезапуск PostgreSQL
sudo systemctl restart postgresql
```

### Шаг 3: Клонирование и настройка проекта

```bash
# Создание пользователя для бота (опционально)
sudo adduser mindbot
sudo usermod -aG sudo mindbot
su - mindbot

# Клонирование проекта (или загрузка архива)
git clone <your-repo-url> /home/mindbot/mind_style_bot
cd /home/mindbot/mind_style_bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 4: Настройка переменных окружения

```bash
# Создание .env файла
cat > .env << 'EOF'
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# База данных
DATABASE_URL=postgresql+asyncpg://mindbot:your_secure_password_123@localhost/mind_style

# Общие настройки
DEBUG=False
ADMIN_USER_ID=your_telegram_user_id

# API сервер для Senler
API_HOST=0.0.0.0
API_PORT=8000
WEBHOOK_URL=https://your-domain.com/senler/webhook
EOF

# Установка правильных прав доступа
chmod 600 .env
```

### Шаг 5: Инициализация базы данных

```bash
# Активация виртуального окружения
source venv/bin/activate

# Создание таблиц
make db-init

# Применение миграции Senler
make db-senler

# Проверка БД
make db-test
```

### Шаг 6: Создание systemd сервисов

#### Сервис для API + Бота

```bash
sudo nano /etc/systemd/system/mindbot-api.service
```

```ini
[Unit]
Description=Mind Style Bot with API
After=network.target postgresql.service

[Service]
Type=simple
User=mindbot
WorkingDirectory=/home/mindbot/mind_style_bot
Environment=PATH=/home/mindbot/mind_style_bot/venv/bin
ExecStart=/home/mindbot/mind_style_bot/venv/bin/python src/run_with_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Альтернативно: отдельные сервисы

```bash
# API сервер
sudo nano /etc/systemd/system/mindbot-api-only.service
```

```ini
[Unit]
Description=Mind Style Bot API Server
After=network.target postgresql.service

[Service]
Type=simple
User=mindbot
WorkingDirectory=/home/mindbot/mind_style_bot
Environment=PATH=/home/mindbot/mind_style_bot/venv/bin
ExecStart=/home/mindbot/mind_style_bot/venv/bin/python src/run_api_only.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Telegram бот
sudo nano /etc/systemd/system/mindbot-telegram.service
```

```ini
[Unit]
Description=Mind Style Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=mindbot
WorkingDirectory=/home/mindbot/mind_style_bot
Environment=PATH=/home/mindbot/mind_style_bot/venv/bin
ExecStart=/home/mindbot/mind_style_bot/venv/bin/python -m src.bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Шаг 7: Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/mindbot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Перенаправление на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL сертификаты (получить через certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Proxy для API сервера
    location /senler/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Основной сайт (если есть)
    location / {
        root /var/www/html;
        index index.html;
    }
}
```

### Шаг 8: Запуск и настройка

```bash
# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Включение сайта
sudo ln -s /etc/nginx/sites-available/mindbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Запуск сервисов
sudo systemctl daemon-reload
sudo systemctl enable mindbot-api
sudo systemctl start mindbot-api

# Проверка статуса
sudo systemctl status mindbot-api
```

### Шаг 9: Проверка деплоя

```bash
# Проверка API
curl https://your-domain.com/health

# Проверка логов
sudo journalctl -u mindbot-api -f

# Тест webhook
curl -X POST https://your-domain.com/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "username": "test_user",
    "token": "test_token_12345"
  }'
```

## Часть 2: Настройка Senler (тестовая воронка)

### Шаг 1: Создание бота в Telegram

1. Найти @BotFather в Telegram
2. Отправить `/newbot`
3. Указать название бота: `Mind Style Test Bot`
4. Указать username: `@your_mindstyle_test_bot`
5. Скопировать токен в `.env` файл

### Шаг 2: Регистрация в Senler

1. Перейти на https://senler.ru/
2. Зарегистрироваться (бесплатный тариф - до 40 сообщений/день)
3. Подключить созданного Telegram бота:
   - Настройки → Telegram → Добавить бота
   - Вставить токен бота
   - Подтвердить подключение

### Шаг 3: Создание тестовой воронки

#### 3.1 Создание нового сценария

1. В Senler: **Сценарии** → **Создать сценарий**
2. Название: "Тест стилей мышления"
3. Триггер: **Команда** `/start`

#### 3.2 Построение цепочки сообщений

**Сообщение 1: Приветствие**
```
🎯 Добро пожаловать!

Я помогу вам определить ваш стиль мышления с помощью психологического тестирования.

📊 Что вас ждет:
• 3 коротких теста
• 15-20 минут времени  
• Персональный анализ результатов

Готовы узнать больше о себе?
```
*Кнопки: "Узнать подробнее" | "Не сейчас"*

**Сообщение 2: Описание тестирования**
```
📋 Подробности тестирования:

🔹 **Тест приоритетов** - определим ваши жизненные ценности
🔹 **Тест стилей мышления** - 18 вопросов о том, как вы принимаете решения  
🔹 **Тест темперамента** - выявим особенности вашей личности

❗ Важно отвечать честно - нет правильных или неправильных ответов!

Результаты помогут лучше понять себя и свои сильные стороны.
```
*Кнопки: "Начать тестирование" | "Назад"*

**Сообщение 3: Переход к внешнему коду**
```
✨ Отлично! Сейчас я передам вас в интерактивную систему тестирования.

⚡ После завершения всех тестов вы автоматически вернетесь сюда и получите:
• Подробный анализ результатов
• Рекомендации по развитию
• Персональные советы

Нажмите кнопку ниже для начала 👇
```
*Кнопка: "🚀 НАЧАТЬ ТЕСТ"*

#### 3.3 Настройка webhook кнопки

Для кнопки **"🚀 НАЧАТЬ ТЕСТ"**:

1. Тип действия: **HTTP запрос** 
2. URL: `https://your-domain.com/senler/webhook`
3. Метод: `POST`
4. Headers: `Content-Type: application/json`
5. Тело запроса:
```json
{
    "user_id": "{{contact.telegram_id}}",
    "username": "{{contact.telegram_username}}",  
    "token": "{{contact.senler_token}}",
    "senler_user_id": "{{contact.id}}"
}
```
6. После запроса: **Завершить диалог**

#### 3.4 Блок возврата из теста

**Сообщение 4: Завершение**
```
🎉 Тестирование завершено!

📊 Ваши результаты уже готовы и сохранены в системе.

🔥 Что дальше?
• Изучите свой профиль мышления
• Используйте рекомендации в работе и жизни
• Поделитесь результатами с близкими

💬 Есть вопросы? Напишите нам!
```
*Кнопки: "Получить рекомендации" | "Поделиться" | "Главное меню"*

### Шаг 4: Настройка переменных в Senler

В Senler нужно настроить переменные для webhook:

1. **{{contact.telegram_id}}** - ID пользователя в Telegram
2. **{{contact.telegram_username}}** - username в Telegram  
3. **{{contact.senler_token}}** - уникальный токен Senler (генерируется автоматически)
4. **{{contact.id}}** - ID контакта в Senler

## Часть 3: Тестирование интеграции

### Шаг 1: Проверка инфраструктуры

```bash
# На сервере: проверка статуса сервисов
sudo systemctl status mindbot-api
sudo systemctl status nginx

# Проверка API endpoints
curl https://your-domain.com/health
curl https://your-domain.com/

# Проверка логов
sudo journalctl -u mindbot-api --since "10 minutes ago"
```

### Шаг 2: Тест Senler воронки

1. **Найти бота в Telegram** (@your_mindstyle_test_bot)
2. **Отправить** `/start`
3. **Пройти по воронке** до кнопки "🚀 НАЧАТЬ ТЕСТ"
4. **Нажать кнопку** - должно произойти:
   - Отправка webhook на ваш сервер
   - Создание записи пользователя в БД
   - Получение стартового сообщения от бота

### Шаг 3: Тест полного цикла

1. **Запуск из Senler** (как в шаге 2)
2. **Прохождение всех тестов**:
   - Ввод имени/фамилии/возраста
   - Тест приоритетов (4 категории)
   - INQ тест (18 вопросов)  
   - EPI тест (57 вопросов)
3. **Получение результатов**
4. **Автоматический возврат** в Senler

### Шаг 4: Мониторинг и логирование

```bash
# Просмотр логов бота в реальном времени
sudo journalctl -u mindbot-api -f

# Проверка соединения с БД
sudo -u mindbot psql mind_style -c "SELECT COUNT(*) FROM users;"

# Nginx логи
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Часть 4: Production настройки

### Безопасность

```bash
# Настройка firewall
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# Ограничение доступа к БД
sudo nano /etc/postgresql/13/main/pg_hba.conf
# Оставить только local соединения

# Backup БД (ежедневно)
sudo crontab -e
# Добавить:
# 0 2 * * * pg_dump mind_style | gzip > /backup/mindbot_$(date +\%Y\%m\%d).sql.gz
```

### Мониторинг

```bash
# Установка htop для мониторинга
sudo apt install htop

# Скрипт проверки работы API
cat > /home/mindbot/check_api.sh << 'EOF'
#!/bin/bash
if ! curl -f https://your-domain.com/health &> /dev/null; then
    echo "API not responding, restarting..."
    sudo systemctl restart mindbot-api
fi
EOF

chmod +x /home/mindbot/check_api.sh

# Добавить в cron (каждые 5 минут)
crontab -e
# */5 * * * * /home/mindbot/check_api.sh
```

### Обновление кода

```bash
# Создать скрипт для обновления
cat > /home/mindbot/update_bot.sh << 'EOF'
#!/bin/bash
cd /home/mindbot/mind_style_bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mindbot-api
echo "Bot updated successfully!"
EOF

chmod +x /home/mindbot/update_bot.sh
```

## Troubleshooting

### Частые проблемы

1. **API не отвечает**
   ```bash
   sudo systemctl status mindbot-api
   sudo journalctl -u mindbot-api --since "1 hour ago"
   ```

2. **Ошибки БД**
   ```bash
   sudo -u postgres psql mind_style
   \dt  # проверка таблиц
   SELECT * FROM users LIMIT 5;
   ```

3. **Senler не может достучаться**
   - Проверить SSL сертификат
   - Проверить firewall  
   - Убедиться что домен резолвится

4. **Webhook не работает**
   - Проверить logs Nginx
   - Проверить формат JSON в Senler
   - Тестировать через curl

### Контакты для поддержки

- **Логи системы**: `sudo journalctl -u mindbot-api -f`
- **Проверка API**: `curl https://your-domain.com/health`
- **Проверка БД**: `make db-test`

---

## 🎯 Итоговый чеклист деплоя

- [ ] Сервер настроен (Python, PostgreSQL, Nginx)
- [ ] SSL сертификат получен
- [ ] Проект клонирован и настроен
- [ ] База данных создана и мигрирована
- [ ] Systemd сервисы настроены и запущены
- [ ] Nginx проксирует запросы
- [ ] Telegram бот создан в BotFather  
- [ ] Senler воронка создана и настроена
- [ ] Webhook тестируется успешно
- [ ] Полный цикл тестирования работает
- [ ] Мониторинг и backup настроены

**После завершения всех пунктов бот готов к продакшену!**