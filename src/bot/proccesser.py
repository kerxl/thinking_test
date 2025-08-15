from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from config.const import PersonalDataStates, MESSAGES, AGE_MAX, AGE_MIN
from src.bot.main import dp
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
            await message.answer(f"❌ Пожалуйста, введите корректный возраст (от {AGE_MIN} до {AGE_MAX} лет)")
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
        test_start=datetime.now(),
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
            inline_keyboard=[[InlineKeyboardButton(text=MESSAGES["button_start"], callback_data="start_tasks")]]
        ),
    )
