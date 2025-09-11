#!/bin/bash
# Скрипт создания systemd сервиса для Mind Style Bot

set -e  # Остановка при ошибках

PROJECT_DIR="/opt/mind_style_bot"
SERVICE_USER="mind_style_bot"
SERVICE_NAME="mind-style-bot"

echo "🔧 Создание systemd сервиса для Mind Style Bot..."

# Создание systemd service файла
echo "📄 Создание systemd service файла..."
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Mind Style Bot - Telegram Bot with Senler Integration
After=network.target mysql.service
Wants=network.target
Requires=mysql.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python src/run_webhook_mode.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Настройки безопасности
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR /var/log/mind_style_bot

# Переменные окружения
Environment=PYTHONPATH=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1

# Лимиты ресурсов
LimitNOFILE=65536
LimitNPROC=32768

[Install]
WantedBy=multi-user.target
EOF"

# Создание скрипта управления сервисом
echo "🎛️ Создание скрипта управления сервисом..."
sudo bash -c "cat > /usr/local/bin/mind-style-bot <<EOF
#!/bin/bash
# Скрипт управления Mind Style Bot

case \"\$1\" in
    start)
        echo \"🚀 Запуск Mind Style Bot...\"
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo \"⏹️ Остановка Mind Style Bot...\"
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo \"🔄 Перезапуск Mind Style Bot...\"
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        echo \"📊 Статус Mind Style Bot:\"
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    logs)
        echo \"📝 Логи Mind Style Bot (последние 50 строк):\"
        sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
        ;;
    logs-follow)
        echo \"📝 Отслеживание логов Mind Style Bot:\"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo \"⚡ Включение автозапуска Mind Style Bot...\"
        sudo systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo \"❌ Отключение автозапуска Mind Style Bot...\"
        sudo systemctl disable $SERVICE_NAME
        ;;
    update-db)
        echo \"🗄️ Обновление схемы базы данных...\"
        cd $PROJECT_DIR
        sudo -u $SERVICE_USER bash -c \"source venv/bin/activate && alembic upgrade head\"
        ;;
    *)
        echo \"Использование: \$0 {start|stop|restart|status|logs|logs-follow|enable|disable|update-db}\"
        echo \"\"
        echo \"Команды:\"
        echo \"  start         - Запустить бота\"
        echo \"  stop          - Остановить бота\"
        echo \"  restart       - Перезапустить бота\"
        echo \"  status        - Показать статус\"
        echo \"  logs          - Показать последние логи\"
        echo \"  logs-follow   - Отслеживать логи в реальном времени\"
        echo \"  enable        - Включить автозапуск\"
        echo \"  disable       - Отключить автозапуск\"
        echo \"  update-db     - Обновить схему БД\"
        exit 1
        ;;
esac
EOF"

# Установка прав на скрипт управления
sudo chmod +x /usr/local/bin/mind-style-bot

# Перезагрузка systemd и включение сервиса
echo "🔄 Перезагрузка systemd daemon..."
sudo systemctl daemon-reload

echo "⚡ Включение автозапуска сервиса..."
sudo systemctl enable $SERVICE_NAME

# Инициализация базы данных
echo "🗄️ Инициализация базы данных..."
cd $PROJECT_DIR
sudo -u $SERVICE_USER bash -c "
    source venv/bin/activate
    alembic upgrade head
"

echo "✅ Systemd сервис настроен успешно!"
echo ""
echo "🎛️ Команды управления:"
echo "   mind-style-bot start       - Запустить бота"
echo "   mind-style-bot stop        - Остановить бота"
echo "   mind-style-bot restart     - Перезапустить бота"
echo "   mind-style-bot status      - Показать статус"
echo "   mind-style-bot logs        - Показать логи"
echo "   mind-style-bot logs-follow - Отслеживать логи"
echo ""
echo "📋 Информация о сервисе:"
echo "   Имя сервиса: $SERVICE_NAME"
echo "   Пользователь: $SERVICE_USER"
echo "   Рабочая директория: $PROJECT_DIR"
echo "   Автозапуск: включен"