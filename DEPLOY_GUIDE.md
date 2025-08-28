# 🚀 Инструкция по запуску Telegram-бота на сервере

## 📋 Что вам понадобится для запуска

### 1. Доступ к серверу
- SSH-доступ к вашему серверу (логин и пароль)
- Права администратора (sudo доступ)

### 2. База данных MySQL
- Имя базы данных (например: `mind_style_bot`)
- Логин пользователя базы данных
- Пароль пользователя базы данных
- Хост базы данных (обычно `localhost`)
- Порт базы данных (обычно `3306`)

### 3. Telegram Bot Token
- Токен бота, который вы получили от @BotFather в Telegram

---

## 🔧 Пошаговая инструкция по запуску

### Шаг 1: Подключение к серверу
1. Откройте программу для SSH-подключения (например, PuTTY на Windows или Terminal на Mac/Linux)
2. Подключитесь к вашему серверу:
   ```
   ssh ваш_логин@ip_адрес_сервера
   ```
3. Введите пароль когда система попросит

### Шаг 2: Перейти в папку с ботом
```bash
cd /путь/к/папке/с/ботом/06.08
```

### Шаг 3: Настройка файла конфигурации
1. Откройте файл настроек:
   ```bash
   nano .env
   ```

2. Заполните следующие данные (замените на свои реальные данные):
   ```
   # Токен вашего Telegram бота
   BOT_TOKEN=ваш_токен_бота_от_BotFather
   
   # Настройки базы данных MySQL
   DATABASE_URL=mysql://пользователь:пароль@localhost:3306/название_базы
   
   # ID администратора бота (ваш Telegram ID)
   ADMIN_USER_ID=ваш_telegram_id
   
   # Режим отладки (для продакшена оставьте false)
   DEBUG=false
   ```

3. Сохраните файл:
   - Нажмите `Ctrl + X`
   - Нажмите `Y` (да)
   - Нажмите `Enter`

### Шаг 4: Установка зависимостей
```bash
# Установка Python зависимостей
pip install -r requirements.txt

# Если pip не найден, сначала установите Python и pip:
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Шаг 5: Создание виртуального окружения
```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей в виртуальном окружении
pip install -r requirements.txt
```

### Шаг 6: Настройка базы данных
```bash
# Создание таблиц в MySQL
mysql -u ваш_пользователь -p ваша_база_данных < database/create_tables.sql

# Добавление полей для Senler интеграции
mysql -u ваш_пользователь -p ваша_база_данных < database/add_admin_senler_link_fields.sql
```

**Альтернативный способ через phpMyAdmin:**
1. Войдите в phpMyAdmin
2. Выберите вашу базу данных
3. Перейдите во вкладку "SQL"
4. Скопируйте и выполните содержимое файла `database/create_tables.sql`
5. Затем скопируйте и выполните содержимое файла `database/add_admin_senler_link_fields.sql`

### Шаг 7: Тестовый запуск
```bash
# Запуск бота для проверки (без API сервера)
python src/bot/main.py
```

Если всё работает корректно, вы увидите сообщения типа:
```
INFO - Bot started successfully
INFO - Listening for messages...
```

Остановите тестовый запуск: `Ctrl + C`

---

## 🌟 Продакшен запуск

### Вариант 1: Запуск только бота
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить бота
make run
```

### Вариант 2: Запуск с API сервером (рекомендуется)
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить бота с API сервером для Senler интеграции
make run-with-api
```

---

## 🔄 Автоматический запуск при перезагрузке сервера

### Создание systemd сервиса
1. Создайте файл сервиса:
   ```bash
   sudo nano /etc/systemd/system/mindstyle-bot.service
   ```

2. Вставьте следующий конфиг (замените пути на свои):
   ```ini
   [Unit]
   Description=Mind Style Telegram Bot
   After=network.target mysql.service
   
   [Service]
   Type=simple
   User=ваш_пользователь
   WorkingDirectory=/полный/путь/к/папке/06.08
   Environment=PATH=/полный/путь/к/папке/06.08/venv/bin
   ExecStart=/полный/путь/к/папке/06.08/venv/bin/python src/run_with_api.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. Сохраните файл (`Ctrl + X`, `Y`, `Enter`)

4. Активируйте сервис:
   ```bash
   # Перезагрузка конфигурации systemd
   sudo systemctl daemon-reload
   
   # Включение автозапуска
   sudo systemctl enable mindstyle-bot.service
   
   # Запуск сервиса
   sudo systemctl start mindstyle-bot.service
   
   # Проверка статуса
   sudo systemctl status mindstyle-bot.service
   ```

---

## 📊 Управление ботом

### Просмотр логов
```bash
# Просмотр логов сервиса
sudo journalctl -u mindstyle-bot.service -f

# Просмотр последних логов
sudo journalctl -u mindstyle-bot.service --lines=50
```

### Управление сервисом
```bash
# Перезапуск бота
sudo systemctl restart mindstyle-bot.service

# Остановка бота
sudo systemctl stop mindstyle-bot.service

# Запуск бота
sudo systemctl start mindstyle-bot.service

# Проверка статуса
sudo systemctl status mindstyle-bot.service
```

---

## 🛠 Возможные проблемы и их решения

### Проблема: "Permission denied" при создании файлов
**Решение:**
```bash
# Дайте права на папку проекта
sudo chown -R ваш_пользователь:ваш_пользователь /путь/к/папке/06.08
```

### Проблема: "ModuleNotFoundError"
**Решение:**
```bash
# Убедитесь что виртуальное окружение активировано
source venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt
```

### Проблема: "Connection refused" к базе данных
**Решение:**
1. Проверьте что MySQL запущен: `sudo systemctl status mysql`
2. Проверьте правильность данных в `.env` файле
3. Убедитесь что база данных создана и пользователь имеет права доступа
4. Попробуйте подключиться к MySQL вручную: `mysql -u пользователь -p база_данных`

### Проблема: Бот не отвечает на сообщения
**Решение:**
1. Проверьте правильность токена в `.env` файле
2. Убедитесь что бот запущен без ошибок
3. Проверьте логи: `sudo journalctl -u mindstyle-bot.service -f`

---

## 📞 Поддержка

Если возникли проблемы:
1. Сохраните вывод команды с ошибкой
2. Сохраните логи: `sudo journalctl -u mindstyle-bot.service --lines=100`
3. Отправьте эту информацию разработчику

---

## ✅ Контрольный список готовности

- [ ] ✅ Проект загружен на сервер
- [ ] ✅ Настроен файл `.env` с правильными данными
- [ ] ✅ База данных MySQL настроена
- [ ] ✅ Установлены зависимости Python
- [ ] ✅ Применены миграции базы данных
- [ ] ✅ Бот успешно запускается
- [ ] ✅ Настроен автозапуск через systemd
- [ ] ✅ Бот отвечает на сообщения в Telegram

**🎉 Поздравляем! Ваш бот готов к работе!**