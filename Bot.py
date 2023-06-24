import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Инициализация бота и диспетчера
bot = Bot(token='6231147103:AAGUuRf8mqQsiBPbHzHW_BgmB07lyyt24f4')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Класс, определяющий состояния бота
class UserForm(StatesGroup):
    name = State()
    question = State()
    contac = State()


# Обработчик ввода текста после нажатия кнопки "Написать"
@dp.message_handler(Text(equals="Написать"))
async def ask_question(message: types.Message):
    # Запуск диалога заново
    await start_command(message)


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # Запуск диалога
    await message.answer("Давайте познакомимся. Как вас зовут?")
    await UserForm.name.set()


@dp.callback_query_handler(text_contains="confirm")
async def confirm_form(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение данных из состояния
    user_data = await state.get_data()

    # Отправка сообщения в канал с данными формы
    channel_message = (
        f"Ник тг: {callback_query.from_user.username}\n"
        f"Имя: {user_data['name']}\n"
        f"Вопрос: {user_data['question']}\n"
        f"Контакты: {user_data['contac']}"
    )
    await bot.send_message(chat_id='-961129183', text=channel_message)

    # Отправка сообщения пользователю о успешной отправке формы
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Остались вопросы? Написать", callback_data="ask_again"))

    await callback_query.message.answer(
            "Спасибо за обращение! Ваш вопрос в обработке, с вами свяжутся в ближайшее время. Обычно это около 24 часов.", reply_markup=keyboard
        )

    # Очистка состояния и переход к начальному состоянию
    await state.finish()

    
@dp.callback_query_handler(text_contains="edit")
async def edit_form(callback_query: types.CallbackQuery, state: FSMContext):
    # Очистка состояния и переход к начальному состоянию
    await state.finish()

    # Запуск диалога заново
    await start_command(callback_query.message)

@dp.callback_query_handler(text_contains="ask_again")
async def ask_form(callback_query: types.CallbackQuery, state: FSMContext):
    # Очистка состояния и переход к начальному состоянию
    await state.finish()

    # Запуск диалога заново
    await start_command(callback_query.message)

# Обработчик ввода имени
@dp.message_handler(state=UserForm.name)
async def process_name(message: types.Message, state: FSMContext):
    # Сохранение имени в состоянии
    await state.update_data(name=message.text)

    # Запрос описания задачи или вопроса
    await message.answer("Спасибо. Теперь опишите максимально подробно вашу задачу или вопрос:")
    await UserForm.next()


# Обработчик ввода задачи или вопроса
@dp.message_handler(state=UserForm.question)
async def process_question(message: types.Message, state: FSMContext):
    # Сохранение задачи или вопроса в состоянии
    await state.update_data(question=message.text)

    # Запрос контактов
    await message.answer("Теперь пожалуйста, поделитесь своими контактами:")
    await UserForm.next()


# Обработчик ввода контактов
@dp.message_handler(state=UserForm.contac)
async def process_contact(message: types.Message, state: FSMContext):
    # Сохранение контактов в состоянии
    await state.update_data(contac=message.text)

    # Получение данных из состояния
    user_data = await state.get_data()

    # Формирование сообщения с готовой формой
    form_message = f"Проверьте, всё ли правильно?\n\nИмя: {user_data['name']}\nВопрос: {user_data['question']}\nКонтакты: {user_data['contac']}"

    # Формирование клавиатуры с кнопками
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Всё верно", callback_data="confirm"),
        InlineKeyboardButton("Редактировать", callback_data="edit")
    )

    # Отправка сообщения с формой и клавиатурой
    await message.answer(form_message, reply_markup=keyboard)

    # Переход к состоянию ожидания подтверждения или редактирования
    await UserForm.next()


if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)