from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
import app.keyboards as kb
import app.httprq as req
import app.jsonopen as jso
from datetime import date

# from app.jsonopen import load_problems as pb_l
# from aiogram.filters.callback_data import CallbackData
# from app.keyboards import ProblemMenu

API_URL = "http://backend:8000/markers/"

router = Router()

# 1. Додаємо стан підтвердження
class ReportProblem(StatesGroup):
    waiting_for_description = State()
    waiting_for_photo = State()
    waiting_for_type = State()
    waiting_for_location = State()
    waiting_for_confirmation = State()

# --- Хендлери ---
@router.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = kb.what_do()
    await message.answer(
        "Привіт! Оберіть дію:",
        reply_markup=keyboard
    )

# Cansel hendler (use for cansel report from any state)
@router.message(StateFilter("*"), F.text.in_({"Скасувати", "❌ Ні, почати заново"}))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer(
        "Дію скасовано. Повертаємось у меню.",
        reply_markup=kb.what_do()
    )

async def get_markers_page_text(markers, page: int, items_per_page: int = 5):
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_markers = markers[start_idx:end_idx]

    response_text = f"<b>Ваші повідомлення (Сторінка {page}):</b>\n\n"
    
    for m in page_markers:
        desc = m.get("description", "Без опису")
        stat = m.get("status")
        typ = m.get("problem_type")
        lat = m.get("geometry_out", {}).get("lat")
        lng = m.get("geometry_out", {}).get("lng")
        timestamp = m.get("timestamp", "")[:10]

        # Отримуємо назву типу (викликаємо вашу функцію з jsonopen)
        type_name = await jso.mapping_problem(str(typ))

        statcod = ""
        if stat == 1:
            statcod = "Заявку отримано"
        elif stat == 2:
            statcod = "Вирішується"
        elif stat == 3:
            statcod = "Вирішено(архів)"
        response_text += (
            f"🆔 №{m.get('id')}\n"
            f"Статус: {statcod}\n"
            f"Тип: {type_name}\n"
            f"📅 Дата: {timestamp}\n"
            f"📝 Опис: {desc}\n"
            f"📍 Координати: {lat}, {lng}\n"
            f"---------------------------\n"
        )
    return response_text

# 3. Оновлений основний хендлер натискання кнопки "Переглянути подані проблеми"
@router.message(F.text == "Переглянути подані проблеми")
async def get_reports(message: Message):
    user_id = message.from_user.id
    markers = await req.get_markers(user_id)

    if markers is None:
        await message.answer("❌ Помилка при отриманні даних з сервера.")
        return
    if not markers:
        await message.answer("У вас поки немає поданих проблем.")
        return

    total_pages = (len(markers) + 4) // 5 # Округлення вгору
    page = 1
    
    text = await get_markers_page_text(markers, page)
    kb_markup = kb.get_pagination_keyboard(page, total_pages)
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb_markup)

# 4. НОВИЙ хендлер для обробки перемикання сторінок (callback)
@router.callback_query(kb.Pagination.filter())
async def process_pagination(callback: types.CallbackQuery, callback_data: kb.Pagination):
    user_id = callback.from_user.id
    markers = await req.get_markers(user_id)
    
    if not markers:
        await callback.answer("Дані більше не доступні.")
        return

    page = callback_data.page
    total_pages = (len(markers) + 4) // 5

    text = await get_markers_page_text(markers, page)
    kb_markup = kb.get_pagination_keyboard(page, total_pages)

    # Редагуємо поточне повідомлення замість надсилання нового
    try:
        await callback.message.edit_text(
            text, 
            parse_mode="HTML", 
            reply_markup=kb_markup
        )
    except Exception:
        # Це виникає, якщо текст повідомлення не змінився (наприклад, натиснули на ту ж сторінку)
        pass
    
    await callback.answer()

@router.message(F.text == "Повідомити про проблему")
async def start_report(message: Message, state: FSMContext):
    await state.set_state(ReportProblem.waiting_for_description)
    await message.answer(
        "Опишіть проблему текстом:",
        reply_markup=kb.cansell_key()
    )


@router.message(ReportProblem.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(problem_text=message.text)
    await state.set_state(ReportProblem.waiting_for_photo)
    await message.answer(
        "Прийнято. Тепер надішліть фото проблеми:",
        reply_markup=kb.cansell_key()
    )


@router.message(ReportProblem.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    bot = message.bot
    file = await bot.get_file(photo_id)
    file_path = file.file_path

    # check if download folder exist
    today = date.today()

    download_dir = f"download/{today.year}/{today.month}"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    destination_path = f"{download_dir}/{photo_id}.jpg"

    await bot.download_file(file_path, destination_path)

    await state.update_data(problem_photo_url=destination_path, problem_photo=photo_id)

    await state.set_state(ReportProblem.waiting_for_type)
    await message.answer(
        "Фото отримано! Тепер оберіть категорію проблеми:",
        reply_markup=kb.get_categories_kb()
    )

# --- НОВІ ХЕНДЛЕРИ ДЛЯ МЕНЮ ТИПІВ ---

# Вибір категорії (Level 0)


@router.callback_query(ReportProblem.waiting_for_type, kb.ProblemMenu.filter(F.level == 0))
async def process_category_click(callback: types.CallbackQuery, callback_data: kb.ProblemMenu, state: FSMContext):
    if callback_data.cat_id == "9":
        problems_data = await jso.load_problems()
        # Виправляємо логіку для "Інше"9
        problem_name = problems_data.get("9")
        await state.update_data(problem_type_id="99", problem_type_name=problem_name)
        await state.set_state(ReportProblem.waiting_for_location)
        await callback.message.answer(f"Обрано: {problem_name}. Тепер надішліть локацію:",
                                      reply_markup=kb.get_location_keyboard())
        await callback.answer()
        return

    await callback.message.edit_text(
        "Оберіть конкретний тип:",
        reply_markup=kb.get_problems_kb(callback_data.cat_id)
    )
    await callback.answer()

# Вибір конкретної проблеми (Level 1)


@router.callback_query(ReportProblem.waiting_for_type, kb.ProblemMenu.filter(F.level == 1))
async def process_problem_click(callback: types.CallbackQuery, callback_data: kb.ProblemMenu, state: FSMContext):
    # Отримуємо назву проблеми зі словника за її ID
    problems_data = await jso.load_problems()
    problem_id = callback_data.prob_id
    problem_name = problems_data.get(problem_id, "Невідома проблема")

    # Зберігаємо вибір у стан
    await state.update_data(problem_type_id=problem_id, problem_type_name=problem_name)

    # Переходимо до наступного кроку — локації
    await state.set_state(ReportProblem.waiting_for_location)

    await callback.message.answer(
        f"Обрано: {problem_name}. Тепер надішліть локацію:",
        reply_markup=kb.get_location_keyboard()
    )
    await callback.answer()

# Кнопка "Назад" (Level -1)


@router.callback_query(ReportProblem.waiting_for_type, kb.ProblemMenu.filter(F.level == -1))
async def process_back_button(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Оберіть категорію проблеми:",
        reply_markup=kb.get_categories_kb()
    )
    await callback.answer()

# --- ЛОГІКА ЗБОРУ ДАНИХ ТА ПІДТВЕРДЖЕННЯ ---

# 1. Обробка локації (якщо надіслали геопозицію)


@router.message(ReportProblem.waiting_for_location, F.location)
async def process_location(message: Message, state: FSMContext):
    # Зберігаємо координати
    lat = message.location.latitude
    lon = message.location.longitude
    await state.update_data(coords=f"{lat}, {lon}")

    # Викликаємо функцію, яка покаже підсумок
    await show_summary(message, state)

# 2. Обробка ручного введення (якщо натиснули "Ввести вручну")


@router.message(ReportProblem.waiting_for_location, F.text == "📝 Ввести вручну")
async def ask_manual_location(message: Message):
    await message.answer("Напишіть координати вручну:")

# 3. Обробка тексту замість локації (якщо ввели вручну)


@router.message(ReportProblem.waiting_for_location, F.text)
async def process_manual_location(message: Message, state: FSMContext):
    # Зберігаємо текст як координати
    await state.update_data(coords=message.text)
    await show_summary(message, state)

# Допоміжна функція для показу підсумку (щоб не дублювати код)


async def show_summary(message: Message, state: FSMContext):
    data = await state.get_data()

    problem_text = data.get("problem_text")
    problem_type = data.get("problem_type_name")
    photo_id = data.get("problem_photo")
    coords = data.get("coords")

    # Формуємо підпис до фото
    caption_text = (
        f"<b>Перевірте дані:</b>\n\n"
        f"📝 <b>Опис:</b> {problem_text}\n"
        f"📝 <b>Тип:</b> {problem_type}\n"
        f"📍 <b>Локація:</b> {coords}\n\n"
        f"<i>Чи все вірно?</i>"
    )

    # Відправляємо фото з описом
    await message.answer_photo(
        photo=photo_id,
        caption=caption_text,
        parse_mode="HTML",
        reply_markup=kb.get_confirmation_keyboard()  # Клавіатура "Так/Ні"
    )

    # Переходимо в стан очікування підтвердження
    await state.set_state(ReportProblem.waiting_for_confirmation)


# --- ФІНАЛ: ЗБЕРЕЖЕННЯ ---

@router.message(ReportProblem.waiting_for_confirmation, F.text == "✅ Все вірно, зберегти")
async def finish_report(message: Message, state: FSMContext):
    data = await state.get_data()

    # 1. Готуємо дані для API
    # Нам потрібно розбити рядок "lat, lon" назад на числа
    coords_str = data.get("coords")
    try:
        lat_str, lng_str = coords_str.split(", ")
        lat, lng = float(lat_str), float(lng_str)
    except (ValueError, AttributeError):

        lat, lng = 0.0, 0.0

    payload = {
        "geometry": {
            "lat": lat,
            "lng": lng
        },
        "description": data.get("problem_text"),
        "photo_id": data.get("problem_photo"),  # Photo id requaire string value
        "user_id": message.from_user.id,
        "problem_type_id": int(data.get("problem_type_id")),
        "timestamp": message.date.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    }
    print(payload)
    response = await req.post_marker(payload)

    if response is None:
        await message.answer("❌ Не вдалося з'єднатися з сервером.")
        return

    if response.status_code == 200:
        await message.answer(
            "✅ Дані успішно збережено в базі!",
            reply_markup=kb.what_do()
        )
        result_data = response.json()
        new_marker_id = result_data.get("id")

        # --- КРОК 3: Відправляємо PUT для оновлення фото ---
        # Передаємо шлях, за яким фронтенд зможе знайти фото
        photo_url_for_db = data.get("problem_photo_url")
        put_response = await req.put_marker(photo_url_for_db, new_marker_id)
        if put_response:
            print("photo sawed")
        await state.clear()
    else:
        await message.answer(f"❌ Помилка сервера: {response.status_code}")


@router.message()
async def handle_other_messages(message: Message):
    await message.answer("Я не розумію. Використовуйте кнопки меню.", reply_markup=kb.what_do())
