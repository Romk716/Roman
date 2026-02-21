# Лабораторная работа №1: [Настройка интегрированной среды разработки]

## Как запустить проект

1. Создайте виртуальное окружение:
   - Windows: `py -m venv .venv`
   - macOS/Linux: `python3 -m venv .venv`

2. Активируйте окружение:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

3. Установите зависимости: `pip install -r requirements.txt`

4. Запустите программу: `python src/app.py`

## Проверка качества кода

- Запуск Ruff: `ruff check .`
- Запуск тестов (если есть): `pytest`

## Правила работы
Подробнее о ветках и коммитах см. [docs/workflow.md](docs/workflow.md).