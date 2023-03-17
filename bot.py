import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext


class GetGroup(StatesGroup):
    pokupka = State()
    clothe_or_sneaker = State()


db = sqlite3.connect("bazaPokupok.db")
sql = db.cursor()
sql.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INT,
    userName TEXT,
    price INT,
    clothe_or_sneakers INT
)""")


bot = Bot(token="")
dp = Dispatcher(bot, storage=MemoryStorage())
pushbutton = types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = types.KeyboardButton("Калькулятор цен 💸")
button2 = types.KeyboardButton("Поддержка 📞")
button3 = types.KeyboardButton("Справка с вопросами ❓")
pushbutton.add(button1, button2, button3)

otmena = types.ReplyKeyboardMarkup(resize_keyboard=True)
otmenabutton = types.KeyboardButton("Отмена")
itog_price_btn = types.KeyboardButton("Итоговая цена")
otmena.add(otmenabutton, itog_price_btn)

cl_or_sn = types.ReplyKeyboardMarkup(resize_keyboard=True)
sneakers_btn = types.KeyboardButton("Обувь")
clothe_btn = types.KeyboardButton("Одежда")
cl_or_sn.add(sneakers_btn, clothe_btn)


@dp.message_handler(Command("start"), state=None)
async def welcome(message):
    if message.from_user.id == message.chat.id:
        sql.execute(f"SELECT * FROM users WHERE user_id = {message.from_user.id}")
        if sql.fetchone() is None:
            sql.execute(f"INSERT INTO users VALUES (?, ?, ?, ?)",
                        (message.from_user.id, message.from_user.username, 0, None))
            db.commit()
        await message.answer("Привет! Добро пожаловать в бот интернет-магазина. Прочитать реальные отзывы покупателей, можно по ссылке - https://vk.com/wall-216021500_1. Для рассчёта стоимости заказа воспользуйся кнопками", reply_markup=pushbutton)


@dp.message_handler(content_types=["text"])
async def qwerty(message):
    if message.text == "Поддержка 📞":
        await message.answer("По вопросам работы бота, а также по вопросам доставки и другим нюансам в личные сообщения @blessed_union")
    elif message.text == "Калькулятор цен 💸":
        await message.answer("Выберете одежда или обувь", reply_markup=cl_or_sn)
        await GetGroup.clothe_or_sneaker.set()
    elif message.text == "Справка с вопросами ❓":
        await message.answer("тут вопросы")
    elif message.text == "Отмена":
        await message.answer("Отменилось", reply_markup=pushbutton)
    elif message.text == "Итоговая цена":
        price = sql.execute(f'SELECT price FROM users WHERE user_id = {message.chat.id}').fetchone()[0]
        await message.answer(f"Ваша итоговая цена: {price}")


@dp.message_handler(state=GetGroup.clothe_or_sneaker)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy():
        await state.finish()
        if message.text == 'Одежда':
            sql.execute(f'UPDATE users SET clothe_or_sneakers = 0 WHERE user_id = "{message.from_user.id}"')
            db.commit()
            await message.answer("Одежда. Отправьте в чат стоимость 1 позиции в ¥", reply_markup=otmena)
            await GetGroup.pokupka.set()
        elif message.text == 'Обувь':
            sql.execute(f'UPDATE users SET clothe_or_sneakers = 1 WHERE user_id = "{message.from_user.id}"')
            db.commit()
            # await message.answer("Обувь. Отправьте в чат стоимость 1 позиции в ¥", reply_markup=types.ReplyKeyboardRemove())
            await message.answer("Обувь. Отправьте в чат стоимость 1 позиции в ¥", reply_markup=otmena)
            await GetGroup.pokupka.set()


@dp.message_handler(state=GetGroup.pokupka)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy():
        await state.finish()
        if message.text == 'Итоговая цена':
            price = sql.execute(f'SELECT price FROM users WHERE user_id = {message.chat.id}').fetchone()[0]
            await message.answer(f"Ваша итоговая цена: {price}", reply_markup=pushbutton)
            sql.execute(f'UPDATE users SET price = 0 WHERE user_id = "{message.from_user.id}"')
            db.commit()
            return

        elif message.text == "Отмена":
            await message.answer("Отменилось", reply_markup=pushbutton)
            sql.execute(f'UPDATE users SET price = 0 WHERE user_id = "{message.from_user.id}"')
            db.commit()
            return

        if sql.execute(f'SELECT clothe_or_sneakers FROM users WHERE user_id = {message.chat.id}').fetchone()[0] == 0:
            await message.answer(f"Сумма твоего заказа - {str(int(message.text) *  11.7 + 3200)} \n \n В стоимость входит выкуп пары, доставка со склада Poizon в Москву, страховка на товар 💣 ")
            last_price = sql.execute(f'SELECT price FROM users WHERE user_id = {message.chat.id}').fetchone()[0]
            sql.execute(f'UPDATE users SET price = {last_price + int(message.text) *  11.7 + 3200} WHERE user_id = "{message.from_user.id}"')
            db.commit()

        elif sql.execute(f'SELECT clothe_or_sneakers FROM users WHERE user_id = {message.chat.id}').fetchone()[0] == 1:
            await message.answer(f"Сумма твоего заказа - {str(int(message.text) *  11.7 + 1000000)} \n \n В стоимость входит выкуп пары, доставка со склада Poizon в Москву, страховка на товар 💣 ")
            last_price = sql.execute(f'SELECT price FROM users WHERE user_id = {message.chat.id}').fetchone()[0]
            sql.execute(f'UPDATE users SET price = {last_price + int(message.text) *  11.7 + 1000000} WHERE user_id = "{message.from_user.id}"')
            db.commit()

        await message.answer(f'Введите еще одно число, если у вас больше заказов')
        await GetGroup.pokupka.set()


async def on_startup(_):
    print("Bot activated")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
