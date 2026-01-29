import json
import os 

# Отримуємо шлях до директорії, де лежить сам jsonopen.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Формуємо шлях до JSON файлу в тій же папці
file_path = os.path.join(current_dir, 'problemTypes.json')

async def load_problems():
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Помилка: Файл не знайдено за шляхом {file_path}")
        return {}


async def mapping_problem(problem_id: str):
    problems = await load_problems()
    for id, name in problems.items():
        if id == problem_id:
            return name

# for id, type in data.items():
#     print(f"id: {id}, problem type: {type}")