import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
import asyncio
from datetime import datetime, timedelta
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

SCHEDULE_FILE = "schedule.json"

def load_schedule():
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_schedule(data):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_days():
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(7)]

@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("👋 Вітаю! Я бот для запису на чергування до пацієнта в лікарні.\n\nКоманди:\n/запис — записатись на чергування\n/графік — переглянути графік\n/скасувати — скасувати свій запис")

@dp.message(Command("графік"))
async def show_schedule(msg: Message):
    schedule = load_schedule()
    if not schedule:
        await msg.answer("📅 Графік поки порожній.")
        return

    text = "<b>Поточний графік чергувань:</b>\n\n"
    for entry in schedule:
        text += f"📅 {entry['date']} — 👤 {entry['user']}\n"
    await msg.answer(text)

@dp.message(Command("запис"))
async def record(msg: Message):
    user_id = msg.from_user.id
    username = msg.from_user.full_name
    schedule = load_schedule()
    booked_dates = [entry["date"] for entry in schedule]

    buttons = []
    for day in get_days():
        if day not in booked_dates:
            buttons.append([types.KeyboardButton(text=day)])

    if not buttons:
        await msg.answer("😔 Немає вільних днів для запису.")
        return

    kb = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    await msg.answer("Оберіть день для чергування:", reply_markup=kb)

    @dp.message()
    async def save_day(message: Message):
        selected_day = message.text.strip()
        if selected_day in booked_dates:
            await message.answer("❌ Цей день уже зайнятий.")
        else:
            schedule.append({"date": selected_day, "user": username, "user_id": user_id})
            save_schedule(schedule)
            await message.answer(f"✅ Ви записались на {selected_day}!", reply_markup=types.ReplyKeyboardRemove())

        dp.message.handlers.unregister(save_day)

@dp.message(Command("скасувати"))
async def cancel(msg: Message):
    user_id = msg.from_user.id
    schedule = load_schedule()
    new_schedule = [entry for entry in schedule if entry["user_id"] != user_id]

    if len(new_schedule) == len(schedule):
        await msg.answer("❌ Ви не маєте записів для скасування.")
    else:
        save_schedule(new_schedule)
        await msg.answer("✅ Ваш запис скасовано.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
