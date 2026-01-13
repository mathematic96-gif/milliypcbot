from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import pandas as pd

import os
API_TOKEN = os.getenv("8139052926:AAE6sy5LI6aovGvblzABHbuA_4Iau4QvVvQ")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ===== СОСТОЯНИЯ ПРОДАЖИ =====
class Sale(StatesGroup):
    photo = State()
    price_usd = State()
    price_uzs = State()
    debt = State()
    debt_date = State()
    debt_sum = State()
    bonus = State()
    extra_items = State()

# ===== СОСТОЯНИЯ ПОИСКА =====
class Search(StatesGroup):
    query = State()

# ===== КНОПКИ =====
main_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add("🛒 Продажа", "💳 Оплата")
main_kb.add("📦 Приход", "🔍 Поиск товаров")

yes_no_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
yes_no_kb.add("Да", "Нет")

# ===== START =====
@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=main_kb)

# ===== ПРОДАЖА =====
@dp.message_handler(text="🛒 Продажа")
async def sale_start(message: types.Message):
    await message.answer("Отправьте фото товара")
    await Sale.photo.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Sale.photo)
async def sale_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Введите цену в долларах ($)")
    await Sale.price_usd.set()

@dp.message_handler(state=Sale.price_usd)
async def sale_price_usd(message: types.Message, state: FSMContext):
    await state.update_data(price_usd=message.text)
    await message.answer("Введите цену в сумах")
    await Sale.price_uzs.set()

@dp.message_handler(state=Sale.price_uzs)
async def sale_price_uzs(message: types.Message, state: FSMContext):
    await state.update_data(price_uzs=message.text)
    await message.answer("Есть долг?", reply_markup=yes_no_kb)
    await Sale.debt.set()

@dp.message_handler(state=Sale.debt)
async def sale_debt(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите дату оплаты долга (например: 20.01.2026)")
        await Sale.debt_date.set()
    else:
        await state.update_data(debt_date="Нет", debt_sum="0")
        await message.answer("Введите бонусы")
        await Sale.bonus.set()

@dp.message_handler(state=Sale.debt_date)
async def sale_debt_date(message: types.Message, state: FSMContext):
    await state.update_data(debt_date=message.text)
    await message.answer("Введите сумму долга")
    await Sale.debt_sum.set()

@dp.message_handler(state=Sale.debt_sum)
async def sale_debt_sum(message: types.Message, state: FSMContext):
    await state.update_data(debt_sum=message.text)
    await message.answer("Введите бонусы")
    await Sale.bonus.set()

@dp.message_handler(state=Sale.bonus)
async def sale_bonus(message: types.Message, state: FSMContext):
    await state.update_data(bonus=message.text)
    await message.answer("Дополнительные купленные товары")
    await Sale.extra_items.set()

@dp.message_handler(state=Sale.extra_items)
async def sale_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(
        f"✅ Продажа сохранена!\n\n"
        f"💵 USD: {data['price_usd']}\n"
        f"💰 UZS: {data['price_uzs']}\n"
        f"📅 Долг: {data['debt_date']}\n"
        f"💸 Сумма долга: {data['debt_sum']}\n"
        f"🎁 Бонус: {data['bonus']}\n"
        f"➕ Доп. товары: {message.text}",
        reply_markup=main_kb
    )
    await state.finish()

# ===== ПОИСК ТОВАРОВ =====
@dp.message_handler(text="🔍 Поиск товаров")
async def search_start(message: types.Message):
    await message.answer("Введите название товара или модель")
    await Search.query.set()

@dp.message_handler(state=Search.query)
async def search_item(message: types.Message, state: FSMContext):
    query = message.text.lower()

    try:
        df = pd.read_excel("PriceList.xlsx")
        results = df[df["model"].str.lower().str.contains(query, na=False)]

        if results.empty:
            await message.answer("❌ Товар не найден", reply_markup=main_kb)
        else:
            text = "🔍 Найденные товары:\n\n"
            for _, row in results.iterrows():
                text += (
                    f"📦 {row['model']}\n"
                    f"💵 USD: {row['price_usd']}\n"
                    f"💰 UZS: {row['price_uzs']}\n\n"
                )

            await message.answer(text, reply_markup=main_kb)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка чтения PriceList.xlsx\n{e}")

    await state.finish()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    executor.start_polling(dp)
