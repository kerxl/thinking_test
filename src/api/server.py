"""
FastAPI сервер для интеграции с Senler
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import json

from src.integration.senler import senler_integration
from src.database.operations import init_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    try:
        await init_db()
        logger.info("✅ API сервер запущен и база данных инициализирована")
        yield
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации API сервера: {e}")
        yield
    finally:
        # Shutdown
        logger.info("🔌 API сервер остановлен")

app = FastAPI(
    title="Mind Style Bot API", 
    description="API для интеграции с Senler",
    lifespan=lifespan
)


class SenlerWebhookRequest(BaseModel):
    """Модель данных webhook запроса от Senler"""

    user_id: int
    username: str
    token: str
    senler_user_id: Optional[str] = None


class WebhookResponse(BaseModel):
    """Модель ответа на webhook"""

    success: bool
    message: str
    user_id: Optional[int] = None
    error: Optional[str] = None




@app.get("/")
async def root():
    """Корневой endpoint для проверки работы сервера"""
    return {"message": "Mind Style Bot API работает"}


@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {"status": "healthy", "service": "mind_style_bot_api"}


@app.post("/senler/debug")
async def senler_debug(request: Request):
    """
    Debug endpoint для анализа данных от Senler
    """
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        logger.info(f"🔍 DEBUG Senler запрос:")
        logger.info(f"   Headers: {headers}")
        logger.info(f"   Body: {body}")
        
        # Попытка парсинга различных форматов
        parsed_data = {}
        
        if body:
            try:
                # JSON
                json_data = json.loads(body)
                parsed_data["json"] = json_data
            except:
                try:
                    # Form data
                    form_data = await request.form()
                    parsed_data["form"] = dict(form_data)
                except:
                    # Raw text
                    parsed_data["text"] = body.decode('utf-8', errors='ignore')
        
        return {
            "success": True,
            "headers": headers,
            "raw_body": body.decode('utf-8', errors='ignore'),
            "parsed_data": parsed_data,
            "content_length": len(body)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "headers": dict(request.headers)
        }


@app.post("/senler/webhook")
async def senler_webhook(request: Request):
    """
    Webhook endpoint для получения запросов от Senler
    Принимает любые данные и логирует их для отладки
    """
    try:
        # Получаем raw данные для анализа
        body = await request.body()
        content_type = request.headers.get("content-type", "unknown")
        
        logger.info(f"📡 Получен запрос от Senler:")
        logger.info(f"   Content-Type: {content_type}")
        logger.info(f"   Raw body: {body}")
        
        # Пытаемся распарсить JSON
        try:
            json_data = await request.json()
            logger.info(f"   JSON данные: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
        except Exception as json_error:
            logger.error(f"   ❌ Ошибка парсинга JSON: {json_error}")
            # Если не JSON, возможно form data
            try:
                form_data = await request.form()
                logger.info(f"   Form данные: {dict(form_data)}")
                json_data = dict(form_data)
            except Exception as form_error:
                logger.error(f"   ❌ Ошибка парсинга Form: {form_error}")
                raise HTTPException(status_code=400, detail="Невозможно распарсить данные")

        # Извлекаем необходимые поля (гибко)
        user_id = None
        username = None
        token = None
        senler_user_id = None

        # Пробуем различные варианты имен полей
        for key, value in json_data.items():
            key_lower = key.lower()
            
            # Пропускаем null значения
            if value is None or str(value).lower() in ['null', 'none', '']:
                continue
                
            if key_lower in ['user_id', 'userid', 'telegram_user_id', 'tg_user_id']:
                try:
                    user_id = int(value)
                except (ValueError, TypeError):
                    logger.warning(f"Невозможно конвертировать {key}={value} в int")
            elif key_lower in ['username', 'user_name', 'telegram_username']:
                username = str(value).strip()
            elif key_lower in ['token', 'senler_token', 'return_token']:
                token = str(value).strip()
            elif key_lower in ['senler_user_id', 'senler_id']:
                senler_user_id = str(value).strip()

        logger.info(f"   Извлеченные данные (до обработки):")
        logger.info(f"     user_id: {user_id}")
        logger.info(f"     username: {username}")
        logger.info(f"     token: {token}")
        logger.info(f"     senler_user_id: {senler_user_id}")

        # УМНАЯ ОБРАБОТКА ОТСУТСТВУЮЩИХ ПОЛЕЙ
        
        # 1. Если user_id отсутствует - пытаемся определить по контексту
        if not user_id:
            logger.warning("🔍 user_id отсутствует, пытаемся определить автоматически...")
            
            # Ищем в других полях возможный user_id
            for key, value in json_data.items():
                if value and str(value).isdigit() and len(str(value)) >= 8:
                    potential_id = int(value)
                    # Telegram user ID обычно от 10 млн и выше
                    if 10000000 <= potential_id <= 9999999999:
                        user_id = potential_id
                        logger.info(f"✅ Автоматически определен user_id: {user_id} из поля '{key}'")
                        break
            
            # Если все еще не найден и есть username - пытаемся найти в БД или получить через Telegram API
            if not user_id and username:
                # Сначала проверяем базу данных
                from src.database.operations import get_user_by_username
                logger.info(f"🔍 Поиск пользователя @{username} в базе данных...")
                existing_user = await get_user_by_username(username)
                
                if existing_user and existing_user.user_id:
                    user_id = existing_user.user_id
                    logger.info(f"✅ Найден пользователь в БД: user_id = {user_id} для @{username}")
                else:
                    logger.info(f"🔍 Пользователь не найден в БД, попытка получить user_id через Telegram API для username: @{username}")
                    telegram_user_id = await senler_integration.get_user_id_by_username(username)
                    if telegram_user_id:
                        user_id = telegram_user_id
                        logger.info(f"✅ Получен user_id через Telegram API: {user_id} для @{username}")
                    else:
                        logger.warning(f"❌ Не удалось получить user_id через Telegram API для @{username}")
            
            # Если все еще не найден - генерируем виртуальный user_id
            if not user_id:
                # Генерируем виртуальный user_id на основе senler_user_id или токена
                import hashlib
                base_string = senler_user_id or token or username or f"senler_unknown_{json_data.get('timestamp', 'default')}"
                hash_object = hashlib.md5(base_string.encode())
                # Генерируем user_id в диапазоне виртуальных ID (начинаем с 99000000)
                user_id = 99000000 + int(hash_object.hexdigest()[:8], 16) % 999999
                logger.warning(f"⚠️  Сгенерирован виртуальный user_id: {user_id} для Senler пользователя")
                logger.warning(f"💡 Основа для генерации: '{base_string}'")
                logger.warning("🔧 В Senler настройте передачу Telegram User ID для корректной работы")

        # 2. Если username отсутствует - генерируем
        if not username or username in ['null', 'None']:
            username = f"senler_user_{user_id}"
            logger.info(f"🏷️  Сгенерирован username: {username}")

        # 3. Если token отсутствует - генерируем уникальный
        if not token or token in ['null', 'None']:
            import uuid
            token = f"senler_token_{uuid.uuid4().hex[:8]}_{user_id}"
            logger.info(f"🎫 Сгенерирован token: {token}")

        logger.info(f"   Финальные данные:")
        logger.info(f"     user_id: {user_id}")
        logger.info(f"     username: {username}")
        logger.info(f"     token: {token}")
        logger.info(f"     senler_user_id: {senler_user_id}")

        # Финальная валидация
        if not user_id:
            raise HTTPException(
                status_code=400, 
                detail="Не удалось определить user_id. Настройте передачу Telegram User ID в Senler"
            )

        # Обрабатываем запрос через Senler Integration
        result = await senler_integration.process_webhook_request(
            user_id=user_id,
            username=username,
            senler_token=token,
        )

        if result["success"]:
            return {
                "success": True, 
                "message": result["message"], 
                "user_id": result["user_id"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        # Пробрасываем HTTP ошибки как есть
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook от Senler: {e}")
        import traceback
        logger.error(f"🐛 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Webhook endpoint для получения обновлений от Telegram
    """
    try:
        # Получаем JSON данные из запроса
        update_data = await request.json()
        
        # Определяем тип обновления
        update_type = "unknown"
        if "message" in update_data:
            update_type = "message"
        elif "callback_query" in update_data:
            update_type = "callback_query"
        elif "inline_query" in update_data:
            update_type = "inline_query"
        elif "channel_post" in update_data:
            update_type = "channel_post"
        
        logger.info(f"📨 Получено {update_type} обновление от Telegram (ID: {update_data.get('update_id')})")
        
        # Логируем детали только для важных событий
        if update_type in ["message", "callback_query"]:
            if update_type == "message":
                msg = update_data["message"]
                user_id = msg.get("from", {}).get("id")
                text = msg.get("text", msg.get("caption", ""))[:50] + "..."
                logger.info(f"   👤 От пользователя {user_id}: '{text}'")
            elif update_type == "callback_query":
                callback = update_data["callback_query"]
                user_id = callback.get("from", {}).get("id")
                data = callback.get("data", "")
                logger.info(f"   🎯 Callback от пользователя {user_id}: '{data}'")
        else:
            # Для остальных типов - краткое логирование
            logger.info(f"   📄 Данные: {json.dumps(update_data, ensure_ascii=False)[:200]}...")
        
        # Импортируем bot и dp локально
        from src.bot.globals import dp, bot
        from aiogram.types import Update
        
        update = Update(**update_data)
        
        logger.info(f"🔄 Обрабатываем {update_type} через dispatcher...")
        
        try:
            await dp.feed_update(bot, update)
            logger.info(f"✅ {update_type.capitalize()} успешно обработано")
        except Exception as dispatch_error:
            # Проверяем, является ли это просто отсутствием обработчика
            error_str = str(dispatch_error)
            if "not handled" in error_str.lower():
                logger.warning(f"⚠️  {update_type.capitalize()} не имеет обработчика (ID: {update_data.get('update_id')})")
                logger.warning(f"   Возможные причины:")
                logger.warning(f"   - Обработчик не зарегистрирован")
                logger.warning(f"   - Неправильный фильтр в обработчике")
                logger.warning(f"   - Состояние FSM не соответствует")
                
                # Добавляем универсальный обработчик для отладки
                await _handle_unhandled_update(update)
            else:
                logger.error(f"❌ Ошибка при обработке {update_type}: {dispatch_error}")
                raise dispatch_error
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook от Telegram: {e}")
        import traceback
        logger.error(f"🐛 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_unhandled_update(update: "Update"):
    """Обрабатывает необработанные обновления для отладки"""
    try:
        from src.bot.globals import bot
        
        if update.message:
            # Если это сообщение без обработчика
            user_id = update.message.from_user.id
            text = update.message.text or update.message.caption or "[медиа]"
            logger.info(f"🤖 Отправляем help сообщение пользователю {user_id}")
            
            await bot.send_message(
                chat_id=user_id,
                text="🤖 Привет! Для начала тестирования нажмите /start"
            )
            
        elif update.callback_query:
            # Если это callback без обработчика
            callback = update.callback_query
            user_id = callback.from_user.id
            data = callback.data
            
            logger.info(f"🎯 Неизвестный callback '{data}' от пользователя {user_id}")
            
            await callback.answer("⚠️ Эта кнопка больше не активна. Начните заново с /start")
            
            # Отправляем новое сообщение с инструкцией
            await bot.send_message(
                chat_id=user_id,
                text="🔄 Похоже, что-то пошло не так. Давайте начнем сначала!\n\nНажмите /start для начала тестирования."
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка в универсальном обработчике: {e}")


@app.post("/senler/establish-contact")
async def establish_contact_with_user(request: Request):
    """
    Endpoint для установки контакта с пользователем через username
    """
    try:
        json_data = await request.json()
        username = json_data.get("username")
        
        if not username:
            raise HTTPException(status_code=400, detail="Username обязателен")
            
        logger.info(f"🤝 Запрос на установку контакта с @{username}")
        
        # Пытаемся установить контакт
        user_id = await senler_integration.try_establish_contact_and_get_user_id(username, establish_contact=True)
        
        if user_id:
            return {
                "success": True,
                "message": f"Контакт установлен с пользователем @{username}",
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "message": f"Не удалось установить контакт с пользователем @{username}",
                "user_id": None
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка установки контакта: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/senler/complete/{user_id}")
async def complete_test_for_senler(user_id: int, message: Optional[str] = None):
    """
    Endpoint для завершения теста и возврата пользователя в Senler

    Args:
        user_id: Telegram user ID
        message: Сообщение для пользователя (опционально)
    """
    try:
        final_message = (
            message or "Спасибо за прохождение теста! Возвращаемся в Senler..."
        )

        success = await senler_integration.return_user_to_senler(user_id, final_message)

        if success:
            return {
                "success": True,
                "message": "Пользователь успешно возвращен в Senler",
            }
        else:
            raise HTTPException(
                status_code=404, detail="Пользователь не найден или нет Senler token"
            )

    except Exception as e:
        logger.error(f"Ошибка завершения теста для пользователя {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
