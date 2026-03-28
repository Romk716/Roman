"""Unit tests for Task Manager."""

import json
import os
import sys

import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from task_service import TaskService, TaskValidationError


@pytest.fixture
def temp_storage(tmp_path):
    """Provides a temporary json storage file path."""
    return str(tmp_path / "test_tasks.json")


def test_create_task_success(temp_storage):
    """TC-01: Создание задачи с валидными данными."""
    service = TaskService(storage_path=temp_storage)
    task = service.create_task(title="Smoke", description="Быстрая проверка", priority=3)

    assert task["id"] == 1
    assert task["title"] == "Smoke"
    assert task["description"] == "Быстрая проверка"
    assert task["status"] == "new"
    assert task["priority"] == 3

    # Check file was written
    assert os.path.exists(temp_storage)
    with open(temp_storage, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["title"] == "Smoke"


def test_create_task_unique_ids(temp_storage):
    """R-01: Уникальность числовых идентификаторов."""
    service = TaskService(storage_path=temp_storage)
    t1 = service.create_task("Задача 1")
    t2 = service.create_task("Задача 2")
    assert t1["id"] != t2["id"]
    assert t2["id"] == t1["id"] + 1


def test_empty_title_validation(temp_storage):
    """TC-10 / TD-09: Попытка создания задачи с пустым названием."""
    service = TaskService(storage_path=temp_storage)
    with pytest.raises(TaskValidationError, match="не может быть пустым"):
        service.create_task("")

    with pytest.raises(TaskValidationError, match="не может быть пустым"):
        service.create_task("   ")


def test_title_boundary_length(temp_storage):
    """TD-01, TD-02, TD-04, TD-05: Граничные значения длины названия (3..30)."""
    service = TaskService(storage_path=temp_storage)

    # 2 chars - should fail
    with pytest.raises(TaskValidationError, match="от 3 до 30"):
        service.create_task("ab")

    # 3 chars - min boundary (valid)
    t_min = service.create_task("abc")
    assert t_min["title"] == "abc"

    # 30 chars - max boundary (valid)
    title_30 = "A" * 30
    t_max = service.create_task(title_30)
    assert t_max["title"] == title_30

    # 31 chars - should fail
    with pytest.raises(TaskValidationError, match="от 3 до 30"):
        service.create_task("A" * 31)


def test_priority_boundary_values(temp_storage):
    """TD-10..TD-14: Граничные значения приоритета (1..5)."""
    service = TaskService(storage_path=temp_storage)

    with pytest.raises(TaskValidationError, match="от 1 до 5"):
        service.create_task("Task Zero", priority=0)

    t1 = service.create_task("Task One", priority=1)
    assert t1["priority"] == 1

    t5 = service.create_task("Task Five", priority=5)
    assert t5["priority"] == 5

    with pytest.raises(TaskValidationError, match="от 1 до 5"):
        service.create_task("Task Six", priority=6)


def test_update_status_valid_and_invalid(temp_storage):
    """TC-03, TC-04 / TD-19..TD-24: Изменение статуса задачи."""
    service = TaskService(storage_path=temp_storage)
    task = service.create_task("Status Task")

    # Valid status
    updated = service.update_task_status(task["id"], "in_progress")
    assert updated["status"] == "in_progress"

    done_task = service.update_task_status(task["id"], "done")
    assert done_task["status"] == "done"

    # Invalid status
    with pytest.raises(TaskValidationError, match="Недопустимый статус"):
        service.update_task_status(task["id"], "отложено")


def test_search_case_insensitive(temp_storage):
    """TC-05: Регистронезависимый поиск по названию и описанию."""
    service = TaskService(storage_path=temp_storage)
    service.create_task("Smoke Task", "Simple")
    service.create_task("PyTest Case", "Unit testing framework")

    # Search in title with lowercase query
    found = service.search_tasks("pytest")
    assert len(found) == 1
    assert found[0]["title"] == "PyTest Case"

    # Search in description
    found_desc = service.search_tasks("framework")
    assert len(found_desc) == 1
    assert found_desc[0]["title"] == "PyTest Case"

    # Search non-existing
    assert len(service.search_tasks("nonexistent")) == 0


def test_persistence_and_recovery(temp_storage):
    """TC-07: Сохранение и восстановление после перезапуска."""
    service1 = TaskService(storage_path=temp_storage)
    service1.create_task("Persist Title", "Persist Description", priority=4)

    # Recreate service simulating app restart
    service2 = TaskService(storage_path=temp_storage)
    tasks = service2.get_all_tasks()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Persist Title"
    assert tasks[0]["description"] == "Persist Description"
    assert tasks[0]["priority"] == 4


def test_missing_and_corrupted_file_recovery(temp_storage):
    """TC-08, TC-09: Поведение при отсутствии и повреждении файла."""
    # File does not exist initially
    service = TaskService(storage_path=temp_storage)
    assert len(service.get_all_tasks()) == 0

    # Write corrupted JSON
    with open(temp_storage, "w", encoding="utf-8") as f:
        f.write("{ damaged json")

    # Normal mode recovers safely with empty list (R-12)
    service_recovering = TaskService(storage_path=temp_storage, demo_defects=False)
    assert len(service_recovering.get_all_tasks()) == 0

    # Saving overwrites corrupted file with valid data
    service_recovering.create_task("Recovered Task")
    with open(temp_storage, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["title"] == "Recovered Task"


def test_demo_defects_behavior(temp_storage):
    """Проверка работы режима демонстрации дефектов (ЛР6, ЛР7, ЛР8)."""
    # Defect #15: Crash with ValueError on empty title
    service_demo = TaskService(storage_path=temp_storage, demo_defects=True)
    with pytest.raises(ValueError, match="empty title not allowed"):
        service_demo.create_task("")

    # Defect #17: Accepts invalid status 'отложено'
    t = service_demo.create_task("Demo Task", "Some description")
    updated = service_demo.update_task_status(t["id"], "отложено")
    assert updated["status"] == "отложено"

    # Defect #19: Description is lost after restart
    service_demo_restarted = TaskService(storage_path=temp_storage, demo_defects=True)
    loaded_task = service_demo_restarted.get_task_by_id(t["id"])
    assert "description" not in loaded_task or loaded_task.get("description") == ""

    # Defect #18: Crashes with JSONDecodeError on corrupted JSON
    with open(temp_storage, "w", encoding="utf-8") as f:
        f.write("{ invalid json")

    with pytest.raises(json.JSONDecodeError):
        TaskService(storage_path=temp_storage, demo_defects=True)