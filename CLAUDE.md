# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot implementing a psychological testing system with three sequential tests:
1. **Priorities Test** - Users rank 4 life categories from 1-5 priority levels
2. **INQ Test** - 18 questions with 5 statements each (thinking styles assessment) 
3. **EPI Test** - 57 yes/no questions (Eysenck Personality Inventory)

The bot integrates with Senler marketing platform and stores comprehensive user data and test results.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (standard mode)
python src/bot/main.py

# Run only API server for Senler integration
python src/run_api_only.py

# Run bot with API server (Senler integration)
python src/run_with_api.py

# Using Makefile
make run              # Standard bot
make run-api         # API server only  
make run-with-api    # Bot + API server
make db-senler       # Apply Senler migration

# Database operations
alembic upgrade head
```

## Architecture

### Core Components

- **TaskManager** (`src/core/task_manager.py`) - Central orchestrator managing test flow, state transitions, and answer processing
- **Test Models** (`src/core/test_models.py`) - Individual test implementations (PrioritiesTask, InqTask, EpiTask) 
- **Database Layer** (`src/database/`) - SQLAlchemy async models and operations
- **Bot Handlers** (`src/bot/`) - Aiogram message/callback handlers

### State Management

- User progress tracked in database (`current_task_type`, `current_question`, `current_step`)
- In-memory active task states managed by TaskManager
- JSON storage for answers (`answers_json`) and calculated scores (`inq_scores_json`, `epi_scores_json`, `priorities_json`)

### Test Flow Architecture

1. **Personal Data Collection** - Name, surname, age with validation
2. **Sequential Test Execution** - Each test has specific completion criteria
3. **Dynamic UI Generation** - Inline keyboards generated based on available options
4. **Answer Processing** - Validation, scoring, and state updates
5. **Results Calculation** - Final scoring and temperament determination

### Key Data Structures

- **User Model** - Comprehensive user data with JSON fields for flexible answer storage
- **TaskEntity Enum** - Test instance registry with scoring algorithms
- **Answer Validation** - Type-specific validation per test (priorities: 1-5 unique scores, INQ: A-E options, EPI: Yes/No)

### Configuration

- Environment variables in `.env` file (BOT_TOKEN, DATABASE_URL, ADMIN_USER_ID)
- Messages and UI text in `constants.json`
- Test questions in JSON files under `questions/` directory
- Constants and enums in `config/const.py`

## Important Notes

- Tests must be completed sequentially - no skipping allowed
- Priorities test requires unique scores (1-5) for 4 categories
- INQ test uses elimination-style selection (5→4→3→2→1 scoring per question)
- EPI test includes temperament calculation based on E/N scores
- Back button functionality only available for INQ test
- All answers stored as JSON for flexibility and future analysis

## Senler Integration

Project now supports integration with Senler marketing platform:

### Key Features
- **Webhook API** (`/senler/webhook`) - receives initialization requests from Senler
- **User Management** - tracks users from Senler with special flags and tokens  
- **Automatic Return** - users are returned to Senler after test completion
- **FastAPI Server** - runs alongside Telegram bot for webhook handling

### Database Changes
Added fields to `users` table:
- `senler_token` - token for returning user to Senler
- `senler_user_id` - Senler system user ID (optional)
- `from_senler` - flag indicating user came from Senler

### Usage
- Run `make db-senler` to apply database migration
- Use `make run-with-api` to start bot + API server
- Use `make run-api` for API server only
- See `SENLER_INTEGRATION.md` for detailed documentation

## AI Assistant Guide
- Общайся со мной на русском языке
- Я разрабатываю проект на Ubuntu 22.04 в Pycharm
- Перед тем как выполнить какую то python команду не забудь активировать venv
- Если создаешь новый файл, то клади его в нужную директорию, если такой нет, то создай
- База данных - Postgresql, для тестирования используй её
- Перед тем как что то думать и делать, взгляни на изменения в гите. Файлы могут переместиться или переименоваться