"""Task service module for managing tasks."""

from __future__ import annotations

import json
import os
from typing import Any

VALID_STATUSES = {"new", "in_progress", "done"}
DEFAULT_FILE_PATH = "tasks.json"


class TaskValidationError(Exception):
    """Raised when task data fails validation in normal mode."""


class TaskService:
    """Service handling task creation, persistence, filtering and searching."""

    def __init__(self, storage_path: str = DEFAULT_FILE_PATH, demo_defects: bool = False) -> None:
        self.storage_path = storage_path
        self.demo_defects = demo_defects
        self.tasks: list[dict[str, Any]] = []
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Loads tasks from storage path.
        
        In normal mode:
        - If file does not exist, starts with empty list (R-11).
        - If file is corrupted, starts with empty list (R-12).
        
        In demo_defects mode (Issue #18):
        - If file is corrupted, raises json.decoder.JSONDecodeError and crashes.
        """
        if not os.path.exists(self.storage_path):
            self.tasks = []
            return

        if self.demo_defects:
            # Issue #18: Crashes on corrupted JSON
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.tasks = data
                else:
                    self.tasks = []
        except (json.JSONDecodeError, OSError):
            # Safe mode on corrupted file
            self.tasks = []

    def _save_tasks(self) -> None:
        """Saves tasks to JSON file.
        
        In demo_defects mode (Issue #19):
        - Drops the 'description' field, reproducing loss of data after restart.
        """
        data_to_save: list[dict[str, Any]] = []
        for task in self.tasks:
            item = {
                "id": task["id"],
                "title": task["title"],
                "status": task["status"],
                "priority": task.get("priority", 3),
            }
            if not self.demo_defects:
                item["description"] = task.get("description", "")
            data_to_save.append(item)

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    def _generate_next_id(self) -> int:
        """Generates the next unique numeric task identifier (R-01)."""
        if not self.tasks:
            return 1
        return max(t["id"] for t in self.tasks) + 1

    def create_task(self, title: str, description: str = "", priority: int = 3) -> dict[str, Any]:
        """Creates a new task with validation and auto-saving (R-00, R-08, R-13, R-14)."""
        # Issue #15 (Lab 7): Crashes with unhandled ValueError if empty title
        if self.demo_defects:
            if not title:
                raise ValueError("empty title not allowed")
        else:
            if not title or not title.strip():
                raise TaskValidationError("Название задачи не может быть пустым.")
            cleaned_title = title.strip()
            if len(cleaned_title) < 3 or len(cleaned_title) > 30:
                raise TaskValidationError(
                    f"Длина названия должна быть от 3 до 30 символов. Текущая длина: {len(cleaned_title)}."
                )

        if not isinstance(priority, int) or priority < 1 or priority > 5:
            raise TaskValidationError("Приоритет должен быть целым числом от 1 до 5.")

        task = {
            "id": self._generate_next_id(),
            "title": title.strip() if not self.demo_defects else title,
            "description": description.strip(),
            "status": "new",
            "priority": priority,
        }
        self.tasks.append(task)
        self._save_tasks()
        return task

    def get_all_tasks(self) -> list[dict[str, Any]]:
        """Returns all tasks (R-02)."""
        return list(self.tasks)

    def get_task_by_id(self, task_id: int) -> dict[str, Any] | None:
        """Finds task by numeric ID (R-03)."""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def update_task_status(self, task_id: int, new_status: str) -> dict[str, Any]:
        """Updates task status and saves changes (R-04, R-05, R-09)."""
        task = self.get_task_by_id(task_id)
        if not task:
            raise TaskValidationError(f"Задача с ID {task_id} не найдена.")

        # Issue #17: In demo mode, accepts invalid statuses like 'отложено'
        normalized_status = new_status.strip().lower()
        if not self.demo_defects and normalized_status not in VALID_STATUSES:
            raise TaskValidationError(
                f"Недопустимый статус '{new_status}'. Допустимые: {', '.join(sorted(VALID_STATUSES))}."
            )

        task["status"] = new_status if self.demo_defects else normalized_status
        self._save_tasks()
        return task

    def filter_by_status(self, status: str) -> list[dict[str, Any]]:
        """Filters tasks by status (R-06)."""
        target = status.strip().lower()
        return [t for t in self.tasks if t["status"].lower() == target]

    def search_tasks(self, keyword: str) -> list[dict[str, Any]]:
        """Searches tasks by keyword in title and description (R-07)."""
        if not keyword:
            return []

        # Issue #16: In demo mode, search is case-sensitive
        if self.demo_defects:
            return [
                t for t in self.tasks
                if keyword in t["title"] or keyword in t.get("description", "")
            ]

        key_lower = keyword.strip().lower()
        return [
            t for t in self.tasks
            if key_lower in t["title"].lower() or key_lower in t.get("description", "").lower()
        ]