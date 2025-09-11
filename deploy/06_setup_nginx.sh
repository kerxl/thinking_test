#!/bin/bash
# Скрипт настройки Nginx для Mind Style Bot webhook

set -e  # Остановка при ошибках

echo "🌐 Настройка Nginx для Mind Style Bot webhook..."

# Запрос домена у пользователя
echo "🌍 Введите домен для webhook (например: yourdomain.com):"
read -r DOMAIN

# Создание конфигурации Nginx для webhook
echo "📝 Создание конфигурации Nginx..."
sudo bash -c "cat > /etc/nginx/sites-available/mind-style-bot <<EOF
# Mind Style Bot Nginx Configuration
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Redirect HTTP to HTTPS
    return 301 https://\\\$server_name\\\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozTLS:10m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security \"max-age=63072000\" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection \"1; mode=block\";
    add_header Referrer-Policy \"strict-origin-when-cross-origin\";

    # Logging
    access_log /var/log/nginx/mind-style-bot-access.log;
    error_log /var/log/nginx/mind-style-bot-error.log;

    # Main webhook endpoint
    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_set_header X-Forwarded-Host \\\$host;
        proxy_set_header X-Forwarded-Port \\\$server_port;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Senler webhook endpoint
    location /senler/webhook {
        proxy_pass http://127.0.0.1:8000/senler/webhook;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_set_header X-Forwarded-Host \\\$host;
        proxy_set_header X-Forwarded-Port \\\$server_port;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        
        access_log off;
    }

    # Deny access to sensitive files
    location ~ /\\.env {
        deny all;
        return 404;
    }

    location ~ /\\.git {
        deny all;
        return 404;
    }

    # Rate limiting for webhook endpoints
    limit_req_zone \\\$binary_remote_addr zone=webhook:10m rate=10r/m;
    
    location ~ ^/(webhook|senler/webhook) {
        limit_req zone=webhook burst=5 nodelay;
    }
}
EOF"

# Активация сайта
echo "🔗 Активация конфигурации Nginx..."
sudo ln -sf /etc/nginx/sites-available/mind-style-bot /etc/nginx/sites-enabled/

# Удаление дефолтной конфигурации если она существует
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "🗑️ Удаление дефолтной конфигурации Nginx..."
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Проверка конфигурации Nginx
echo "✅ Проверка конфигурации Nginx..."
sudo nginx -t

# Создание скрипта установки SSL сертификата
echo "🔐 Создание скрипта установки SSL сертификата..."
sudo bash -c "cat > /usr/local/bin/setup-ssl-mind-style-bot <<EOF
#!/bin/bash
# Скрипт установки SSL сертификата для Mind Style Bot

set -e

DOMAIN=\"$DOMAIN\"

echo \"🔐 Установка SSL сертификата для \\\$DOMAIN...\"

# Установка Certbot если не установлен
if ! command -v certbot &> /dev/null; then
    echo \"📦 Установка Certbot...\"
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Получение SSL сертификата
echo \"📋 Получение SSL сертификата от Let's Encrypt...\"
sudo certbot --nginx -d \\\$DOMAIN -d www.\\\$DOMAIN --non-interactive --agree-tos --email admin@\\\$DOMAIN

# Настройка автообновления
echo \"⏰ Настройка автообновления сертификата...\"
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo \"✅ SSL сертификат установлен успешно!\"
echo \"🔄 Перезагрузка Nginx...\"
sudo systemctl reload nginx

echo \"🌐 Домен \\\$DOMAIN готов к работе с HTTPS!\"
EOF"

# Установка прав на скрипт SSL
sudo chmod +x /usr/local/bin/setup-ssl-mind-style-bot

# Перезагрузка Nginx
echo "🔄 Перезагрузка Nginx..."
sudo systemctl reload nginx

# Включение автозапуска Nginx
echo "⚡ Включение автозапуска Nginx..."
sudo systemctl enable nginx

echo "✅ Nginx настроен успешно!"
echo ""
echo "🔧 Следующие шаги:"
echo "   1. Настройте DNS записи для домена $DOMAIN"
echo "   2. Запустите: setup-ssl-mind-style-bot"
echo "   3. Проверьте webhook: https://$DOMAIN/webhook"
echo ""
echo "📋 Информация:"
echo "   Домен: $DOMAIN"
echo "   Webhook URL: https://$DOMAIN/webhook"
echo "   Senler webhook: https://$DOMAIN/senler/webhook"
echo "   Health check: https://$DOMAIN/health"
echo "   Конфигурация: /etc/nginx/sites-available/mind-style-bot"