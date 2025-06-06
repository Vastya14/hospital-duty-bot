import logging
import json
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from aiogram import F
from aiogram.filters import CommandStart, Command

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

SCHEDULE_FILE = "schedule.json"
SHIFT_TYPES = ["До обіду", "Після обіду"]

# Завантаження/збереження графіка
def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return {}
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

# /start
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("👋 Вітаю! Я бот для запису на чергування до пацієнта.\n\n"
                         "Використовуйте команду /zapys щоб записатись.")

# /zapys — вибір дати
@dp.message(Command("zapys"))
async def choose_date(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    today = datetime.today()
    for i in range(7):
        day = today + timedelta(days=i)
        label = day.strftime("%d.%m (%a)")
        callback_data = day.strftime("date:%Y-%m-%d")
        keyboard.button(text=label, callback_data=callback_data)
    keyboard.adjust(2)
    await message.answer("🗓 Оберіть дату чергування:", reply_markup=keyboard.as_markup())

# Обробка вибору дати
@dp.callback_query(F.data.startswith("date:"))
async def choose_shift_type(callback: types.CallbackQuery):
    date_str = callback.data.split(":")[1]
    kb = InlineKeyboardBuilder()
    for shift in SHIFT_TYPES:
        kb.button(text=shift, callback_data=f"shift:{date_str}:{shift}")
    await callback.message.edit_text(f"🕔 Оберіть зміну на {date_str}:", reply_markup=kb.as_markup())

# Обробка вибору зміни
@dp.callback_query(F.data.startswith("shift:"))
async def confirm_shift(callback: types.CallbackQuery):
    _, date_str, shift_type = callback.data.split(":")
    user = callback.from_user
    user_fullname = f"{user.first_name} {user.last_name or ''}".strip()

    schedule = load_schedule()
    if date_str not in schedule:
        schedule[date_str] = {}

    current = schedule[date_str].get(shift_type)

    if current:
        if current == user_fullname:
            await callback.message.edit_text(f"⚠️ Ви вже записані на {shift_type} {date_str}.")
        else:
            await callback.message.edit_text(f"❌ Ця зміна вже зайнята: {hbold(current)}.")
    else:

