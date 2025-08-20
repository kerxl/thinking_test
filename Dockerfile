# Multi-stage build для оптимизации размера образа
FROM python:3.9-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production образ
FROM python:3.9-slim

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование виртуального окружения из builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создание пользователя для приложения (безопасность)
RUN groupadd -r mindbot && useradd -r -g mindbot mindbot

# Создание рабочей директории
WORKDIR /app

# Копирование кода приложения
COPY --chown=mindbot:mindbot . .

# Создание директории для логов
RUN mkdir -p /app/logs && chown mindbot:mindbot /app/logs

# Переключение на пользователя приложения
USER mindbot

# Открытие порта для API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск приложения
CMD ["python", "src/run_with_api.py"]