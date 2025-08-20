# 🧪 Руководство по тестированию Mind Style Bot + Senler

## Обзор

Этот документ описывает как протестировать полную интеграцию бота с платформой Senler и убедиться, что все компоненты работают корректно.

## Предварительные условия

### Что должно быть готово:
- ✅ Бот задеплоен на сервере
- ✅ API сервер запущен и отвечает
- ✅ База данных PostgreSQL настроена
- ✅ SSL сертификат установлен  
- ✅ Senler воронка создана
- ✅ Telegram бот создан в @BotFather

## Этап 1: Проверка инфраструктуры

### 1.1 Проверка сервера

```bash
# На сервере выполните:
./check_status.sh

# Ожидаемый результат:
# ✅ Service status: Active (running)
# ✅ API Health: {"status": "healthy"}
# ✅ Last log entries показывают нормальную работу
```

### 1.2 Проверка API endpoints

```bash
# Health check
curl https://your-domain.com/health
# Ожидается: {"status":"healthy","service":"mind_style_bot_api"}

# Корневой endpoint  
curl https://your-domain.com/
# Ожидается: {"message":"Mind Style Bot API работает"}

# API документация
curl https://your-domain.com/docs
# Должна открываться Swagger UI документация
```

### 1.3 Проверка базы данных

```bash
# На сервере:
sudo -u postgres psql mind_style -c "
SELECT 
    schemaname, tablename, tableowner 
FROM pg_tables 
WHERE schemaname = 'public';
"

# Ожидается таблица 'users' с нужными полями
sudo -u postgres psql mind_style -c "
\d users
"

# Проверка Senler полей:
# senler_token, senler_user_id, from_senler должны присутствовать
```

## Этап 2: Тестирование Senler webhook

### 2.1 Ручной тест webhook

```bash
# Тест с корректными данными
curl -X POST https://your-domain.com/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 987654321,
    "username": "test_senler_user",
    "token": "test_senler_token_abc123",
    "senler_user_id": "senler_12345"
  }'

# Ожидаемый ответ:
# {
#   "success": true,
#   "message": "Пользователь успешно инициализирован",
#   "user_id": 987654321
# }
```

### 2.2 Проверка создания пользователя в БД

```bash
# Проверить, что пользователь создался
sudo -u postgres psql mind_style -c "
SELECT user_id, username, senler_token, from_senler 
FROM users 
WHERE user_id = 987654321;
"

# Ожидается:
# user_id: 987654321
# username: test_senler_user  
# senler_token: test_senler_token_abc123
# from_senler: true
```

### 2.3 Тест невалидных данных

```bash
# Тест без обязательного поля user_id
curl -X POST https://your-domain.com/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "token": "token"}'

# Ожидается HTTP 422 (Validation Error)

# Тест с некорректным JSON
curl -X POST https://your-domain.com/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{"invalid": json}'

# Ожидается HTTP 400 (Bad Request)
```

## Этап 3: Тестирование в Senler

### 3.1 Проверка настроек в Senler

1. **Войдите в Senler админку**
2. **Откройте ваш сценарий** "Тест стилей мышления"
3. **Проверьте кнопку "🚀 НАЧАТЬ ТЕСТ"**:
   - Тип действия: HTTP запрос
   - URL: `https://your-domain.com/senler/webhook` 
   - Метод: POST
   - Content-Type: application/json
   - Тело запроса содержит переменные Senler

### 3.2 Тест с реальным пользователем

1. **Найдите бота в Telegram** (@your_bot_name)
2. **Отправьте `/start`**
3. **Пройдите по воронке Senler** до кнопки тестирования
4. **Нажмите "🚀 НАЧАТЬ ТЕСТ"**

**Ожидаемое поведение:**
- Получите новое сообщение от бота вне Senler интерфейса
- Сообщение содержит приветствие и кнопку "Начать"
- Бот "выходит" из визуального сценария Senler

### 3.3 Проверка логов при реальном тесте

```bash
# Следите за логами во время теста
./view_logs.sh

# Ожидаемые записи:
# INFO: Получен webhook от Senler для пользователя XXXXX
# INFO: Пользователь XXXXX инициализирован из Senler  
# INFO: Стартовое сообщение отправлено пользователю XXXXX
```

## Этап 4: Тестирование полного цикла

### 4.1 Прохождение всех тестов

После успешного запуска из Senler:

1. **Ввод личных данных**:
   - Имя и фамилия
   - Возраст (от 12 до 99)

2. **Тест приоритетов**:
   - Выставьте оценки от 1 до 5 для 4 категорий
   - Каждая оценка должна быть уникальной

3. **INQ тест (18 вопросов)**:
   - По 5 утверждений в каждом вопросе
   - Распределите баллы от 5 до 1
   - Проверьте работу кнопки "Назад"

4. **EPI тест (57 вопросов)**:  
   - Вопросы "Да/Нет"
   - Прохождение всех 57 вопросов

### 4.2 Проверка завершения и возврата в Senler

После завершения всех тестов:

**Ожидаемое поведение для пользователей из Senler:**
- Показываются результаты тестирования
- Отображается сообщение "Спасибо за прохождение теста!"
- НЕТ кнопки "Начать заново" (в отличие от обычных пользователей)
- Пользователь "возвращается" в Senler (логически)

### 4.3 Проверка сохранения данных

```bash
# Проверьте, что все данные сохранились
sudo -u postgres psql mind_style -c "
SELECT 
    user_id,
    username, 
    first_name,
    last_name, 
    age,
    from_senler,
    test_completed,
    temperament,
    inq_scores_json IS NOT NULL as has_inq_scores,
    epi_scores_json IS NOT NULL as has_epi_scores,
    priorities_json IS NOT NULL as has_priorities
FROM users 
WHERE from_senler = true 
ORDER BY created_at DESC 
LIMIT 5;
"
```

## Этап 5: Тестирование граничных случаев

### 5.1 Тест повторного запуска

1. **Найдите того же пользователя в Telegram**
2. **Запустите тест из Senler повторно**
3. **Проверьте поведение**:
   - Пользователь должен начать тест заново
   - Предыдущие результаты должны сохраниться в БД
   - Новый тест должен обновить данные

### 5.2 Тест с недоступным Telegram API

```bash
# Временно заблокируйте доступ к Telegram API
sudo iptables -A OUTPUT -d api.telegram.org -j DROP

# Попробуйте запустить webhook
curl -X POST https://your-domain.com/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{"user_id": 111111111, "username": "test", "token": "token"}'

# Ожидается:
# - Пользователь создается в БД  
# - API возвращает success, но в логах ошибка отправки сообщения
# - Система остается стабильной

# Восстановите доступ
sudo iptables -D OUTPUT -d api.telegram.org -j DROP
```

### 5.3 Тест нагрузки

```bash
# Простой тест нагрузки (несколько одновременных запросов)
for i in {1..10}; do
  curl -X POST https://your-domain.com/senler/webhook \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": $((100000 + i)), \"username\": \"user$i\", \"token\": \"token$i\"}" &
done
wait

# Проверьте, что все пользователи создались
sudo -u postgres psql mind_style -c "
SELECT COUNT(*) FROM users WHERE user_id BETWEEN 100001 AND 100010;
"
# Ожидается: 10
```

## Этап 6: Тестирование мониторинга

### 6.1 Проверка health check

```bash
# Автоматическая проверка каждые 30 секунд
while true; do
  if curl -f https://your-domain.com/health &>/dev/null; then
    echo "$(date): ✅ API healthy"
  else
    echo "$(date): ❌ API unhealthy"
  fi
  sleep 30
done
```

### 6.2 Проверка логирования

```bash
# Проверьте, что логи записываются
tail -f /var/log/mindbot/app.log

# Или через journald
sudo journalctl -u mindbot-api -f --since "10 minutes ago"
```

## Этап 7: Тестирование аварийных сценариев

### 7.1 Перезапуск сервисов

```bash
# Перезапуск API сервера
sudo systemctl restart mindbot-api
sleep 10
curl https://your-domain.com/health

# Перезапуск PostgreSQL  
sudo systemctl restart postgresql
sleep 30
curl https://your-domain.com/health

# Перезапуск Nginx
sudo systemctl restart nginx
curl https://your-domain.com/health
```

### 7.2 Тест восстановления после сбоя

```bash
# Искусственный сбой API
sudo systemctl stop mindbot-api

# Проверка автоматического перезапуска (через systemd)
sleep 60
sudo systemctl status mindbot-api

# Должен перезапуститься автоматически через RestartSec=10
```

## Чеклист успешного тестирования

### ✅ Инфраструктура
- [ ] API сервер отвечает на health check
- [ ] База данных доступна и содержит нужные таблицы  
- [ ] SSL сертификат работает
- [ ] Nginx проксирует запросы корректно

### ✅ Senler интеграция  
- [ ] Webhook принимает и обрабатывает запросы
- [ ] Пользователи создаются в БД с правильными флагами
- [ ] Стартовые сообщения отправляются в Telegram
- [ ] Невалидные запросы обрабатываются корректно

### ✅ Полный цикл тестирования
- [ ] Запуск теста из Senler воронки работает
- [ ] Все три теста проходятся без ошибок  
- [ ] Результаты сохраняются в БД
- [ ] Пользователи из Senler корректно завершают тестирование
- [ ] Обычные пользователи видят кнопку "Начать заново"

### ✅ Надежность
- [ ] Система восстанавливается после перезапусков
- [ ] Логирование работает правильно
- [ ] Нагрузочное тестирование проходит успешно
- [ ] Граничные случаи обрабатываются

## Troubleshooting

### Частые проблемы и решения

**❌ API не отвечает**
```bash
sudo systemctl status mindbot-api
sudo journalctl -u mindbot-api --since "1 hour ago"
```

**❌ Webhook возвращает 500**
```bash
./view_logs.sh
# Проверьте подключение к БД и правильность переменных окружения
```

**❌ Сообщения не отправляются в Telegram**
```bash
# Проверьте BOT_TOKEN в .env
# Проверьте доступность api.telegram.org
curl https://api.telegram.org/botYOUR_TOKEN/getMe
```

**❌ Senler воронка не работает**
- Проверьте правильность webhook URL
- Убедитесь, что переменные {{contact.telegram_id}} доступны
- Проверьте формат JSON в HTTP запросе

## Контакты для поддержки

При проблемах с тестированием:
1. Проверьте логи: `./view_logs.sh`
2. Проверьте статус: `./check_status.sh`  
3. Обратитесь к DEPLOYMENT_GUIDE.md
4. Посмотрите SENLER_INTEGRATION.md

---

**🎯 После успешного прохождения всех тестов система готова к продакшену!**