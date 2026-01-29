from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
# from app.jsonopen import load_problems as pb_l
import app.jsonopen as pb_l
# Дані з JSON
PROBLEMS = {
    "10": "Забруднення водойм", "11": "Забруднення повітря",
    "12": "Забруднення ґрунту/хімікатами", "13": "Шумове забруднення",
    "20": "Несанкціоноване сміттєзвалище", "21": "Проблема вивозу побутового сміття",
    "22": "Промислові/токсичні відходи", "30": "Стихійне лихо (повінь/пожежа)",
    "31": "Техногенна катастрофа/аварія", "32": "Вибухонебезпечний предмет (ВНП)",
    "40": "Незаконна вирубка лісів", "41": "Загроза біорізноманіттю",
    "42": "Виснаження ресурсів", "50": "Прорив каналізації/забруднення стоками",
    "51": "Прорив тепломереж", "99": "Інше / Невизначена проблема"
}

CATEGORIES = {
    "1": "🌍 Забруднення",
    "2": "🗑 Відходи",
    "3": "⚠️ Екстрені ситуації",
    "4": "🌳 Природа",
    "5": "🔧 Комунальні",
    "9": "❓ Інше"
}

class ProblemMenu(CallbackData, prefix="prob"):
    level: int    # 0 - вибір категорії, 1 - вибір проблеми
    cat_id: str
    prob_id: str = "0"

def get_categories_kb():
    builder = InlineKeyboardBuilder()
    for cid, cname in CATEGORIES.items():
        builder.add(InlineKeyboardButton(
            text=cname, 
            callback_data=ProblemMenu(level=0, cat_id=cid).pack())
        )
    builder.adjust(2)
    return builder.as_markup()

def get_problems_kb(cat_id: str):
    builder = InlineKeyboardBuilder()
    problems_data = pb_l.load_problems()
    # Фільтруємо проблеми, що починаються з цифри категорії (наприклад "1")
    for pid, pname in problems_data.items():
        if pid.startswith(cat_id):
            builder.add(InlineKeyboardButton(
                text=pname,
                callback_data=ProblemMenu(level=1, cat_id=cat_id, prob_id=pid).pack())
            )
    
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=ProblemMenu(level=-1, cat_id="0").pack()))
    builder.adjust(1)
    return builder.as_markup()

def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Все вірно, зберегти")],
            [KeyboardButton(text="❌ Ні, почати заново")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb

def cansell_key() -> ReplyKeyboardMarkup:

    #1. Create button
    cansell_button = KeyboardButton(
        text="Скасувати"
    )

    # 
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[cansell_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def what_do() -> ReplyKeyboardMarkup:

    # 1. Create buttons
    problem_button = KeyboardButton(
        text="Повідомити про проблему"
    )
    see_problems = KeyboardButton(
        text="Переглянути подані мною проблеми"
    )

    # 2. Create keyboard
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [problem_button],
            [see_problems]
        ],
        resize_keyboard=True, # Chane keyboard size to small
        input_field_placeholder="Що будемо робити."
    )
    return keyboard

# Creating keyboard for geting geolocation
def get_location_keyboard() -> ReplyKeyboardMarkup:
    
    # 1. create buttons
    geo_button = KeyboardButton(
        text="📍 Поділитися геолокацією",
        request_location=True # Main parameter for geting location
    )
    text_button = KeyboardButton(
        text="📝 Ввести вручну"
    )
    
    # 2. Create keyboard
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [geo_button],
            [text_button]
        ],
        resize_keyboard=True, # Chane keyboard size to small
        input_field_placeholder="Оберіть спосіб введення..."
    )
    return keyboard


class Pagination(CallbackData, prefix="pag"):
    page: int

def get_pagination_keyboard(page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Назад"
    if page > 1:
        builder.add(InlineKeyboardButton(
            text="⬅️ Попередня", 
            callback_data=Pagination(page=page - 1).pack())
        )
    
    # Інформаційна кнопка (поточна сторінка)
    builder.add(InlineKeyboardButton(
        text=f"{page}/{total_pages}", 
        callback_data="current_page") # Вона нічого не робить
    )

    # Кнопка "Вперед"
    if page < total_pages:
        builder.add(InlineKeyboardButton(
            text="Наступна ➡️", 
            callback_data=Pagination(page=page + 1).pack())
        )

    builder.adjust(3) # Розташувати в один ряд
    return builder.as_markup()