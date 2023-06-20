import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Command


# Конфигурация логгирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token='6231147103:AAGUuRf8mqQsiBPbHzHW_BgmB07lyyt24f4')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Определение состояний
class Form(StatesGroup):
    name = State()
    question = State()


# Обработчик команды /start
@dp.message_handler(Command('start'))
async def cmd_start(message: types.Message):
    await Form.name.set()
    await message.reply("Давайте познакомимся. Как вас зовут?")


# Обработчик ответа на вопрос "Как вас зовут?"
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    
    await Form.next()
    await message.reply("Спасибо. Теперь опишите максимально подробно вашу задачу или вопрос:")


# Обработчик ответа на вопрос "Опишите вашу задачу или вопрос"
@dp.message_handler(state=Form.question)
async def process_question(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text
    
    # Готовая форма для отправки
    form_text = (
        f"Проверьте, всё ли правильно?\n\n"
        f"Имя: {data['name']}\n"
        f"Вопрос: {data['question']}"
    )

    # Кнопки "Всё верно", "Редактировать" и "Остались вопросы? Написать"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Всё верно", callback_data="confirm"),
        types.InlineKeyboardButton("Редактировать", callback_data="edit")
    )

    await message.reply(form_text, reply_markup=keyboard)


# Обработчик нажатия на кнопку "Всё верно" или "Редактировать"
@dp.callback_query_handler(lambda c: c.data in ["confirm", "edit", "ask_again"], state="*")
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "confirm":
        await callback_query.answer()
        async with state.proxy() as data:
            # Отправка сообщения в специальный канал
            await bot.send_message(
                -961129183,  # Замените на ID вашего канала
                f"Ник тг: @{callback_query.from_user.username}\n"
                f"Имя: {data['name']}\n"
                f"Вопрос: {data['question']}"
            )
        

        # Кнопка "Остались вопросы? Написать" в виде инлайновой кнопки
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Остались вопросы? Написать", callback_data="ask_again"))

        await callback_query.message.answer(
            "Спасибо за обращение! Ваш вопрос в обработке, с вами свяжутся в ближайшее время. Обычно это около 24 часов.", reply_markup=keyboard
        )

        await state.finish()
    
    elif callback_query.data == "edit":
        await callback_query.answer()
        await Form.name.set()
        await callback_query.message.answer("Давайте познакомимся. Как вас зовут?")
    
    elif callback_query.data == "ask_again":
        await Form.name.set()
        await callback_query.message.answer("Давайте познакомимся. Как вас зовут?")


# Обработчик команды /cancel
@dp.message_handler(Command('cancel'), state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await message.answer("Вы отменили ввод.")
    await state.finish()


if __name__ == '__main__':
    from aiogram import executor

    # Запуск бота
    executor.start_polling(dp, skip_updates=True)