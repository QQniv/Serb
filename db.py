import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

DB_PATH = Path("largo.db")


def get_connection() -> sqlite3.Connection:
    """Возвращает подключение к БД."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Создаёт таблицы, если их ещё нет."""
    conn = get_connection()
    cur = conn.cursor()

    # Таблица задач
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            due_at TEXT,          -- ISO datetime
            status TEXT NOT NULL DEFAULT 'active',  -- active / done / canceled
            created_at TEXT NOT NULL
        )
        """
    )

    # Таблица заметок / идей (на будущее)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'idea',  -- idea / note / other
            created_at TEXT NOT NULL
        )
        """
    )

    # Настройки пользователя (час напоминаний и т.п.)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            morning_hour INTEGER DEFAULT 9,      -- час утреннего дайджеста
            evening_hour INTEGER DEFAULT 21      -- час вечернего отчёта
        )
        """
    )

    conn.commit()
    conn.close()


# ---------- TASKS ----------


def add_task(
    user_id: int,
    text: str,
    due_at: Optional[datetime] = None,
) -> int:
    """Создаёт задачу и возвращает её id."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tasks (user_id, text, due_at, status, created_at)
        VALUES (?, ?, ?, 'active', ?)
        """,
        (
            user_id,
            text,
            due_at.isoformat() if due_at else None,
            datetime.utcnow().isoformat(),
        ),
    )

    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_active_tasks(user_id: int) -> List[sqlite3.Row]:
    """Все активные задачи пользователя."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, text, due_at, status
        FROM tasks
        WHERE user_id = ?
          AND status = 'active'
        ORDER BY
          CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,
          due_at ASC
        """,
        (user_id,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def get_due_tasks(now_utc: datetime) -> List[sqlite3.Row]:
    """Задачи, по которым пора напомнить (простая версия)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, user_id, text, due_at
        FROM tasks
        WHERE status = 'active'
          AND due_at IS NOT NULL
          AND due_at <= ?
        """,
        (now_utc.isoformat(),),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def mark_task_done(task_id: int) -> None:
    """Помечает задачу выполненной."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE tasks SET status = 'done' WHERE id = ?",
        (task_id,),
    )

    conn.commit()
    conn.close()


# ---------- NOTES ----------


def add_note(user_id: int, text: str, note_type: str = "idea") -> int:
    """Добавляет заметку/идею."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO notes (user_id, text, type, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            text,
            note_type,
            datetime.utcnow().isoformat(),
        ),
    )

    note_id = cur.lastrowid
    conn.commit()
    conn.close()
    return note_id


def get_notes(user_id: int, note_type: Optional[str] = None) -> List[sqlite3.Row]:
    """Возвращает заметки / идеи пользователя."""
    conn = get_connection()
    cur = conn.cursor()

    if note_type:
        cur.execute(
            """
            SELECT id, text, type, created_at
            FROM notes
            WHERE user_id = ? AND type = ?
            ORDER BY created_at DESC
            """,
            (user_id, note_type),
        )
    else:
        cur.execute(
            """
            SELECT id, text, type, created_at
            FROM notes
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

    rows = cur.fetchall()
    conn.close()
    return rows
