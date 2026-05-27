"""待办事项管理模块
支持添加、删除、查看待办事项，以及定时检查和提醒
"""

import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="[Todo] %(message)s")
logger = logging.getLogger("TodoManager")


class TodoItem:
    """单个待办事项"""

    def __init__(
        self,
        title: str,
        due_time: datetime,
        todo_id: str | None = None,
        created_at: datetime | None = None,
        completed: bool = False,
        notified: bool = False,
    ):
        self.id = todo_id or uuid.uuid4().hex[:8]
        self.title = title
        self.due_time = due_time
        self.created_at = created_at or datetime.now()
        self.completed = completed
        self.notified = notified  # 是否已经提醒过

    @property
    def is_due(self) -> bool:
        """检查是否到期（未完成、未提醒、且当前时间 >= 到期时间）"""
        if self.completed or self.notified:
            return False
        return datetime.now() >= self.due_time

    @property
    def is_past(self) -> bool:
        """检查是否已过期（仅用于显示，不管是否提醒过）"""
        return datetime.now() > self.due_time

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "due_time": self.due_time.strftime("%Y-%m-%d %H:%M"),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "completed": self.completed,
            "notified": self.notified,
        }

    @staticmethod
    def from_dict(d: dict) -> "TodoItem":
        return TodoItem(
            title=d["title"],
            due_time=datetime.strptime(d["due_time"], "%Y-%m-%d %H:%M"),
            todo_id=d.get("id"),
            created_at=datetime.strptime(
                d.get("created_at", "2024-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"
            ),
            completed=d.get("completed", False),
            notified=d.get("notified", False),
        )

    def __repr__(self):
        return (
            f"TodoItem(id={self.id}, title={self.title!r}, "
            f"due={self.due_time.strftime('%Y-%m-%d %H:%M')}, "
            f"completed={self.completed}, notified={self.notified})"
        )


class TodoManager:
    """待办事项管理器（单例）"""

    def __init__(self):
        self._todos: list[TodoItem] = []
        self._storage_path = self._get_storage_path()
        self.load()

    def _get_storage_path(self) -> Path:
        """获取存储路径（兼容 PyInstaller 打包）"""
        import sys
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent
        return base / "todos.json"

    # ---------- CRUD ----------

    def add(self, title: str, due_time: datetime) -> TodoItem:
        """添加待办事项"""
        item = TodoItem(title=title, due_time=due_time)
        self._todos.append(item)
        self.save()
        logger.info(f"Added todo: {item}")
        return item

    def remove(self, todo_id: str) -> bool:
        """删除待办事项"""
        for i, item in enumerate(self._todos):
            if item.id == todo_id:
                self._todos.pop(i)
                self.save()
                logger.info(f"Removed todo: {item}")
                return True
        return False

    def complete(self, todo_id: str) -> bool:
        """标记待办事项为完成"""
        for item in self._todos:
            if item.id == todo_id:
                item.completed = True
                self.save()
                logger.info(f"Completed todo: {item}")
                return True
        return False

    def mark_notified(self, todo_id: str) -> bool:
        """标记待办事项已提醒"""
        for item in self._todos:
            if item.id == todo_id:
                item.notified = True
                self.save()
                return True
        return False

    # ---------- 查询 ----------

    def get_all(self, include_completed: bool = True) -> list[TodoItem]:
        """获取所有待办事项"""
        if include_completed:
            return list(self._todos)
        return [t for t in self._todos if not t.completed]

    def get_active(self) -> list[TodoItem]:
        """获取活跃（未完成）的待办事项"""
        return [t for t in self._todos if not t.completed]

    def get_due_todos(self) -> list[TodoItem]:
        """获取已到期但未提醒的待办事项"""
        return [t for t in self._todos if t.is_due]

    def parse_and_add(self, title: str, time_str: str) -> TodoItem | None:
        """
        解析时间字符串并添加待办事项
        支持格式：
        - YYYY-MM-DD HH:MM
        - HH:MM (默认今天)
        - 相对时间："30分钟后", "1小时后", "明天 15:00"
        """
        import re
        try:
            # 尝试完整日期时间
            due_time = datetime.strptime(time_str.strip(), "%Y-%m-%d %H:%M")
            return self.add(title, due_time)
        except ValueError:
            pass

        try:
            # 尝试今天的时间
            today = datetime.now().strftime("%Y-%m-%d")
            due_time = datetime.strptime(
                f"{today} {time_str.strip()}", "%Y-%m-%d %H:%M"
            )
            # 如果时间已过，设为明天
            if due_time <= datetime.now():
                from datetime import timedelta
                due_time += timedelta(days=1)
            return self.add(title, due_time)
        except ValueError:
            pass

        # 相对时间解析
        now = datetime.now()
        from datetime import timedelta

        # "30分钟后"
        match = re.search(r'(\d+)\s*分钟后', time_str)
        if match:
            minutes = int(match.group(1))
            return self.add(title, now + timedelta(minutes=minutes))

        # "1小时后"
        match = re.search(r'(\d+)\s*小时后', time_str)
        if match:
            hours = int(match.group(1))
            return self.add(title, now + timedelta(hours=hours))

        # "明天 HH:MM"
        match = re.search(r'明天\s*(\d{1,2}):(\d{2})', time_str)
        if match:
            h, m = int(match.group(1)), int(match.group(2))
            tomorrow = now + timedelta(days=1)
            due_time = tomorrow.replace(hour=h, minute=m, second=0, microsecond=0)
            return self.add(title, due_time)

        # "今天 HH:MM"
        match = re.search(r'今天\s*(\d{1,2}):(\d{2})', time_str)
        if match:
            h, m = int(match.group(1)), int(match.group(2))
            due_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if due_time <= now:
                due_time += timedelta(days=1)
            return self.add(title, due_time)

        logger.warning(f"Could not parse time string: {time_str!r}")
        return None

    # ---------- 持久化 ----------

    def save(self):
        """保存到 JSON 文件"""
        data = [item.to_dict() for item in self._todos]
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save todos: {e}")

    def load(self):
        """从 JSON 文件加载"""
        if not self._storage_path.exists():
            self._todos = []
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._todos = [TodoItem.from_dict(d) for d in data]
            logger.info(f"Loaded {len(self._todos)} todos")
        except Exception as e:
            logger.error(f"Failed to load todos: {e}")
            self._todos = []


# 全局单例
_todo_manager: TodoManager | None = None


def get_todo_manager() -> TodoManager:
    """获取全局 TodoManager 单例"""
    global _todo_manager
    if _todo_manager is None:
        _todo_manager = TodoManager()
    return _todo_manager