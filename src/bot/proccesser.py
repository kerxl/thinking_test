from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from config.const import PersonalDataStates, AdminStates, MESSAGES, AGE_MAX, AGE_MIN
from .globals import dp
from src.database.operations import get_or_create_user, update_user


@dp.message(PersonalDataStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name_parts = message.text.strip().split()
    if len(name_parts) < 2:
        await message.answer(MESSAGES["name_input_call"])
        return

    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])

    if len(first_name) < 2 or len(last_name) < 2:
        await message.answer(MESSAGES["name_input_format_error"])
        return

    await state.update_data(first_name=first_name, last_name=last_name)
    await message.answer(
        f"✅ Имя: <b>{first_name} {last_name}</b>\n\n"
        f"2️⃣ Напишите свой возраст. Эта информация поможет адаптировать вашего персонального бота.\n\n"
        f"📝 Шаг: 2 / 2"
    )
    await state.set_state(PersonalDataStates.waiting_for_age)


@dp.message(PersonalDataStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if age < AGE_MIN or age > AGE_MAX:
            await message.answer(
                f"❌ Пожалуйста, введите корректный возраст (от {AGE_MIN} до {AGE_MAX} лет)"
            )
            return
    except ValueError:
        await message.answer(MESSAGES["age_type_error"])
        return

    data = await state.get_data()

    # Создание пользователя
    user = await get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=data["first_name"],
        last_name=data["last_name"],
    )

    await update_user(
        user_id=message.from_user.id,
        first_name=data["first_name"],
        last_name=data["last_name"],
        age=age,
        task_start=datetime.now(),
    )

    await state.clear()

    await message.answer(
        f"✅ <b>Данные сохранены!</b>\n\n"
        f"👤 Имя: {data['first_name']} {data['last_name']}\n"
        f"🎂 Возраст: {age} лет\n\n"
        f"Мы создаём бота, который будет настроен именно под вас.\n\n"
        f"Для этого нужно пройти три теста. Там нет правильных и неправильных ответов — отвечайте максимально искренне.\n\n"
        f"Если готовы — нажимайте кнопку «Начать».",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=MESSAGES["button_start"], callback_data="start_tasks"
                    )
                ]
            ]
        ),
    )


@dp.message(AdminStates.waiting_for_senler_link)
async def process_admin_senler_link(message: Message, state: FSMContext):
    """
    Обработка ввода ссылки Senler от администратора
    """
    # Проверяем, что это админ
    from config.settings import ADMIN_USER_ID

    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("❌ У вас нет прав для выполнения этого действия")
        await state.clear()
        return

    # Получаем данные из состояния
    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        await message.answer("❌ Ошибка: не найден ID пользователя")
        await state.clear()
        return

    senler_link = message.text.strip()

    # Простая валидация ссылки
    if not senler_link.startswith(("http://", "https://")):
        await message.answer(
            "❌ Пожалуйста, введите корректную ссылку (должна начинаться с http:// или https://)"
        )
        return

    # Сохраняем только ссылку, время отправки уже установлено при завершении теста
    from sqlalchemy import select, update as sql_update
    from src.database.models import AsyncSessionLocal, User

    async with AsyncSessionLocal() as db_session:
        # Получаем информацию о пользователе
        result = await db_session.execute(
            select(User).where(User.user_id == target_user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден")
            await state.clear()
            return

        # Обновляем только ссылку
        await db_session.execute(
            sql_update(User)
            .where(User.user_id == target_user_id)
            .values(admin_senler_link=senler_link)
        )
        await db_session.commit()

    # Проверяем, есть ли уже установленное время отправки
    if user.admin_link_send_time:
        send_time_text = user.admin_link_send_time.strftime("%d.%m.%Y %H:%M:%S")
        await message.answer(
            f"✅ <b>Ссылка сохранена!</b>\n\n"
            f"🔗 Ссылка: {senler_link}\n"
            f"👤 Пользователь: {target_user_id}\n"
            f"📅 Запланировано к отправке: {send_time_text}\n\n"
            f"Ссылка будет автоматически отправлена пользователю в назначенное время."
        )
    else:
        await message.answer(
            f"✅ <b>Ссылка сохранена!</b>\n\n"
            f"🔗 Ссылка: {senler_link}\n"
            f"👤 Пользователь: {target_user_id}\n\n"
            f"⚠️ <b>Внимание:</b> У пользователя не установлено время отправки ссылки. "
            f"Возможно, он еще не завершил тесты или пришел из Senler."
        )

    await state.clear()
