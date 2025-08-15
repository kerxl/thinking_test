# Makefile for Telegram Bot Development

.PHONY: help install test run check clean setup

# Путь к виртуальному окружению
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Полная настройка проекта (создание venv, установка зависимостей)
	@echo "$(GREEN)Создание виртуального окружения...$(NC)"
	python3 -m venv $(VENV)
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Настройка завершена!$(NC)"
	@echo "$(YELLOW)Не забудьте настроить .env файл$(NC)"

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	$(PIP) install -r requirements.txt

test: ## Запустить все тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	$(PYTHON) -m pytest

test-verbose: ## Запустить тесты с подробным выводом
	@echo "$(GREEN)Запуск тестов (подробный режим)...$(NC)"
	$(PYTHON) -m pytest -v

test-unit: ## Запустить только unit тесты
	@echo "$(GREEN)Запуск unit тестов...$(NC)"
	$(PYTHON) -m pytest -m unit

test-integration: ## Запустить только интеграционные тесты
	@echo "$(GREEN)Запуск интеграционных тестов...$(NC)"
	$(PYTHON) -m pytest -m integration

test-coverage: ## Запустить тесты с покрытием кода
	@echo "$(GREEN)Запуск тестов с покрытием...$(NC)"
	$(PIP) install pytest-cov
	$(PYTHON) -m pytest --cov=src --cov-report=html

check: ## Проверить готовность системы
	@echo "$(GREEN)Проверка готовности системы...$(NC)"
	$(PYTHON) check_system.py

run: ## Запустить бота
	@echo "$(GREEN)Запуск бота...$(NC)"
	$(PYTHON) src/bot/main.py

run-debug: ## Запустить бота в режиме отладки
	@echo "$(GREEN)Запуск бота (режим отладки)...$(NC)"
	DEBUG=True $(PYTHON) src/bot/main.py

clean: ## Очистить временные файлы
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

lint: ## Проверить код линтером (если установлен)
	@if [ -f "$(VENV)/bin/flake8" ]; then \
		echo "$(GREEN)Проверка кода линтером...$(NC)"; \
		$(PYTHON) -m flake8 src/; \
	else \
		echo "$(YELLOW)flake8 не установлен. Установка...$(NC)"; \
		$(PIP) install flake8; \
		$(PYTHON) -m flake8 src/; \
	fi

format: ## Форматировать код (если установлен black)
	@if [ -f "$(VENV)/bin/black" ]; then \
		echo "$(GREEN)Форматирование кода...$(NC)"; \
		$(PYTHON) -m black src/ tests/; \
	else \
		echo "$(YELLOW)black не установлен. Установка...$(NC)"; \
		$(PIP) install black; \
		$(PYTHON) -m black src/ tests/; \
	fi

db-init: ## Инициализировать базу данных
	@echo "$(GREEN)Инициализация базы данных...$(NC)"
	$(PYTHON) -c "import asyncio; from src.database.operations import init_db; asyncio.run(init_db())"

requirements: ## Обновить requirements.txt
	@echo "$(GREEN)Обновление requirements.txt...$(NC)"
	$(PIP) freeze > requirements.txt

activate: ## Показать команду активации виртуального окружения
	@echo "$(GREEN)Для активации виртуального окружения выполните:$(NC)"
	@echo "source $(VENV)/bin/activate"

deactivate: ## Показать команду деактивации виртуального окружения
	@echo "$(GREEN)Для деактивации виртуального окружения выполните:$(NC)"
	@echo "deactivate"

# База данных
db-setup: ## Полная настройка базы данных (создание + таблицы + тестовые данные)
	@echo "$(GREEN)Настройка базы данных...$(NC)"
	./database/db_manager.sh setup

db-create: ## Создать базу данных и пользователя
	@echo "$(GREEN)Создание базы данных...$(NC)"
	./database/db_manager.sh create-db

db-tables: ## Создать таблицы
	@echo "$(GREEN)Создание таблиц...$(NC)"
	./database/db_manager.sh create-tables

db-clean: ## Очистить все данные в базе данных
	@echo "$(GREEN)Очистка базы данных...$(NC)"
	./database/db_manager.sh clean

db-sample: ## Добавить тестовые данные
	@echo "$(GREEN)Добавление тестовых данных...$(NC)"
	./database/db_manager.sh sample-data

db-test: ## Проверить подключение к базе данных
	@echo "$(GREEN)Проверка подключения к БД...$(NC)"
	./database/db_manager.sh test

db-backup: ## Создать бэкап базы данных
	@echo "$(GREEN)Создание бэкапа...$(NC)"
	./database/db_manager.sh backup

db-restore: ## Восстановить базу данных из бэкапа
	@echo "$(GREEN)Восстановление из бэкапа...$(NC)"
	./database/db_manager.sh restore

db-stats: ## Показать статистику базы данных
	@echo "$(GREEN)Статистика базы данных...$(NC)"
	./database/db_manager.sh stats

db-connect: ## Подключиться к базе данных интерактивно
	@echo "$(GREEN)Подключение к базе данных...$(NC)"
	./database/db_manager.sh connect

# Проверка существования виртуального окружения
$(VENV)/bin/python:
	@echo "$(RED)Виртуальное окружение не найдено!$(NC)"
	@echo "$(YELLOW)Выполните: make setup$(NC)"
	@exit 1

# Установка зависимостей по умолчанию при первом запуске
.DEFAULT: $(VENV)/bin/python