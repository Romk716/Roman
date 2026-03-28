"""Command line interface for Task Manager."""

from __future__ import annotations

import argparse

from task_service import DEFAULT_FILE_PATH, TaskService, TaskValidationError


def print_menu(demo_mode: bool) -> None:
    mode_str = " [РЕЖИМ ДЕМОНСТРАЦИИ ДЕФЕКТОВ (ЛР7/ЛР8)]" if demo_mode else ""
    print("\n" + "=" * 50)
    print(f"   СЕРВИС ЗАДАЧ (Task Manager){mode_str}")
    print("=" * 50)
    print("Команды:")
    print("  add               - Создать новую задачу")
    print("  list              - Показать все задачи")
    print("  find <слово>      - Поиск по ключевому слову")
    print("  filter <статус>   - Фильтр по статусу (new, in_progress, done)")
    print("  status <id> <st>  - Изменить статус задачи")
    print("  help              - Показать справку")
    print("  exit              - Выйти из программы")
    print("=" * 50)


def print_tasks_table(tasks: list[dict]) -> None:
    if not tasks:
        print("Список задач пуст.")
        return

    print("-" * 75)
    print(f"{'ID':<4} | {'Заголовок':<25} | {'Статус':<12} | {'Приоритет':<9} | {'Описание'}")
    print("-" * 75)
    for t in tasks:
        title = (t["title"][:22] + "...") if len(t["title"]) > 25 else t["title"]
        desc = t.get("description", "")
        desc_short = (desc[:25] + "...") if len(desc) > 28 else desc
        print(f"{t['id']:<4} | {title:<25} | {t['status']:<12} | {t.get('priority', 3):<9} | {desc_short}")
    print("-" * 75)


def handle_add(service: TaskService, demo_mode: bool) -> None:
    # Prompts exactly matching Lab 7 reproduction steps
    title = input("Enter title: ")
    description = input("Enter description: ")

    if demo_mode:
        input("Нажмите Enter для подтверждения создания задачи: ")
        # Issue #15 (Lab 7): Crash with unhandled ValueError
        if not title:
            raise ValueError("empty title not allowed")
        task = service.create_task(title=title, description=description)
        print(f"Задача #{task['id']} успешно создана.")
        return

    # Normal mode: safe validation
    cleaned_title = title.strip()
    if not cleaned_title:
        print("Ошибка: название задачи не может быть пустым.")
        return

    priority_str = input("Enter priority (1-5, default 3): ").strip()
    priority = 3
    if priority_str:
        try:
            priority = int(priority_str)
        except ValueError:
            print("Ошибка: приоритет должен быть целым числом от 1 до 5.")
            return

    try:
        task = service.create_task(title=cleaned_title, description=description, priority=priority)
        print(f"Задача #{task['id']} успешно создана и сохранена.")
    except TaskValidationError as err:
        print(f"Ошибка валидации: {err}")


def handle_status(service: TaskService, args: list[str]) -> None:
    if len(args) < 2:
        id_str = input("Введите ID задачи: ").strip()
        new_status = input("Введите новый статус (new, in_progress, done): ").strip()
    else:
        id_str, new_status = args[0], args[1]

    try:
        task_id = int(id_str)
    except ValueError:
        print("Ошибка: ID задачи должен быть целым числом.")
        return

    try:
        task = service.update_task_status(task_id, new_status)
        print(f"Статус задачи #{task['id']} обновлен на '{task['status']}'.")
    except TaskValidationError as err:
        print(f"Ошибка: {err}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Учебный модуль 'Сервис задач'")
    parser.add_argument(
        "--demo-defects",
        action="store_true",
        help="Запуск в режиме демонстрации дефектов для лабораторных работ 6, 7 и 8",
    )
    parser.add_argument(
        "--storage",
        default=DEFAULT_FILE_PATH,
        help="Путь к файлу хранилища задач (по умолчанию tasks.json)",
    )
    args = parser.parse_args()

    demo_mode = args.demo_defects

    # In demo mode, corrupted JSON crashes on init (Issue #18)
    service = TaskService(storage_path=args.storage, demo_defects=demo_mode)

    print_menu(demo_mode)

    while True:
        try:
            user_input = input("\nВведите команду > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nВыход из программы.")
            break

        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].lower()
        cmd_args = parts[1:]

        if command == "exit":
            print("Работа завершена. До свидания!")
            break
        elif command == "help":
            print_menu(demo_mode)
        elif command == "list":
            tasks = service.get_all_tasks()
            print_tasks_table(tasks)
        elif command == "add":
            handle_add(service, demo_mode)
        elif command == "find":
            keyword = " ".join(cmd_args) if cmd_args else input("Введите ключевое слово для поиска: ").strip()
            results = service.search_tasks(keyword)
            print(f"Результаты поиска по запросу '{keyword}':")
            print_tasks_table(results)
        elif command == "filter":
            target_status = cmd_args[0] if cmd_args else input("Введите статус для фильтрации: ").strip()
            results = service.filter_by_status(target_status)
            print(f"Задачи со статусом '{target_status}':")
            print_tasks_table(results)
        elif command == "status" or command == "done":
            handle_status(service, cmd_args)
        else:
            print(f"Неизвестная команда: '{command}'. Введите 'help' для списка команд.")


if __name__ == "__main__":
    main()