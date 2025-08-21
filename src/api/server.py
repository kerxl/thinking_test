"""
FastAPI сервер для интеграции с Senler
"""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.integration.senler import senler_integration
from src.database.operations import init_db

logger = logging.getLogger(__name__)

app = FastAPI(title="Mind Style Bot API", description="API для интеграции с Senler")


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


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервера"""
    try:
        await init_db()
        logger.info("✅ API сервер запущен и база данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации API сервера: {e}")


@app.get("/")
async def root():
    """Корневой endpoint для проверки работы сервера"""
    return {"message": "Mind Style Bot API работает"}


@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {"status": "healthy", "service": "mind_style_bot_api"}


@app.post("/senler/webhook", response_model=WebhookResponse)
async def senler_webhook(request: SenlerWebhookRequest):
    """
    Webhook endpoint для получения запросов от Senler

    Принимает:
    - user_id: Telegram user ID
    - username: Telegram username
    - token: Token для возврата пользователя в Senler
    - senler_user_id: ID пользователя в системе Senler (опционально)
    """
    try:
        logger.info(
            f"Получен webhook от Senler: user_id={request.user_id}, username={request.username}"
        )

        # Обрабатываем запрос через Senler Integration
        result = await senler_integration.process_webhook_request(
            user_id=request.user_id,
            username=request.username,
            senler_token=request.token,
        )

        if result["success"]:
            return WebhookResponse(
                success=True, message=result["message"], user_id=result["user_id"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Ошибка обработки webhook от Senler: {e}")
        raise HTTPException(
            status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


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
