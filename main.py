from config import TOKEN

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Класс для состояний
class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()


# Функция для инициализации базы данных
def init_db():
    try:
        with sqlite3.connect('school_data.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                age INTEGER NOT NULL,
                grade TEXT NOT NULL)
            ''')
            conn.commit()
    except sqlite3.DatabaseError as e:
        logging.error(f"Ошибка при создании базы данных: {e}")


# Инициализация базы данных
init_db()


# Кнопки для ввода нового ученика и вывода всей таблицы
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ввести нового ученика", callback_data="new_student")],
        [InlineKeyboardButton(text="Показать все ученики", callback_data="show_all_students")]
    ])
    return keyboard


# Команда /start
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Что ты хочешь сделать?", reply_markup=get_main_menu())


# Обработчик кнопки "Ввести нового ученика"
@dp.callback_query(lambda c: c.data == 'new_student')
async def process_new_student(call, state: FSMContext):
    await call.message.answer("Привет! Как тебя зовут?")
    await state.set_state(Form.name)


# Обработчик кнопки "Показать все ученики"
@dp.callback_query(lambda c: c.data == 'show_all_students')
async def process_show_all_students(call, state: FSMContext):
    try:
        with sqlite3.connect('school_data.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            all_users = cursor.fetchall()

            if all_users:
                user_data_str = "\n".join(
                    [f"ID: {user[0]}, Имя: {user[1]}, Возраст: {user[2]}, Класс: {user[3]}" for user in all_users])
            else:
                user_data_str = "Нет данных о пользователях."

            await call.message.answer(f"Все ученики:\n{user_data_str}")
    except sqlite3.DatabaseError as e:
        logging.error(f"Ошибка при работе с базой данных: {e}")
        await call.message.answer("Произошла ошибка при получении данных.")


# Состояние для имени
@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите ваше имя.")
        return
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)


# Состояние для возраста
@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный возраст (число).")
        return
    await state.update_data(age=message.text)
    await message.answer("В каком классе ты учишься?")
    await state.set_state(Form.grade)


# Состояние для класса
@dp.message(Form.grade)
async def grade(message: Message, state: FSMContext):
    school_data = await state.get_data()

    if not message.text:
        await message.answer("Пожалуйста, укажите ваш класс.")
        return

    await state.update_data(grade=message.text)

    try:
        student_age = int(school_data['age'])
    except ValueError:
        await message.answer("Ошибка: возраст должен быть числом.")
        return

    try:
        with sqlite3.connect('school_data.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, age, grade) VALUES (?, ?, ?)",
                           (school_data['name'], student_age, message.text))
            conn.commit()

        await message.answer(f"Данные о ученике {school_data['name']} сохранены.")

    except sqlite3.DatabaseError as e:
        logging.error(f"Ошибка при работе с базой данных: {e}")
        await message.answer("Произошла ошибка при сохранении данных.")

    await state.clear()
    await message.answer("Что ты хочешь сделать?", reply_markup=get_main_menu())


# Основная функция для запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
