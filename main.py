from config import TOKEN

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
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
        conn = sqlite3.connect('school_data.db')
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
    finally:
        conn.close()


# Инициализация базы данных
init_db()


# Команда /start
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    await state.set_state(Form.name)


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
    # Получаем данные пользователя из состояния
    school_data = await state.get_data()

    # Проверяем, что класс указан
    if not message.text:
        await message.answer("Пожалуйста, укажите ваш класс.")
        return

    # Обновляем класс в состоянии
    await state.update_data(grade=message.text)

    # Преобразуем возраст в целое число
    try:
        age = int(school_data['age'])
    except ValueError:
        await message.answer("Ошибка: возраст должен быть числом.")
        return

    # Сохраняем данные в базе данных
    try:
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, age, grade) VALUES (?, ?, ?)",
                       (school_data['name'], age, message.text))
        conn.commit()

        # После сохранения данных извлекаем все записи
        cursor.execute("SELECT * FROM users")
        all_users = cursor.fetchall()

        # Формируем строку с данными всех пользователей
        user_data_str = "\n".join(
            [f"ID: {user[0]}, Имя: {user[1]}, Возраст: {user[2]}, Класс: {user[3]}" for user in all_users])

        await message.answer(f"Данные сохранены!\n\nВсе пользователи:\n{user_data_str}")

    except sqlite3.DatabaseError as e:
        logging.error(f"Ошибка при работе с базой данных: {e}")
        await message.answer("Произошла ошибка при сохранении данных.")
    finally:
        conn.close()

    # Очищаем состояние
    await state.clear()


# Основная функция для запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
