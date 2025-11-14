import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from config import TELEGRAM_BOT_TOKEN
import db


# --- Инициализация бота и диспетчера ---

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


# --- Команды ---


@dp.message(CommandStart())
async def cmd_start(message: Message):
    db.init_db()  # на всякий случай, если БД ещё не создана

    await message.answer(
        "Привет! Я твой ИИ-секретарь.\n\n"
        "Пиши мне всё, что нужно запомнить:\n"
        "• задачи\n"
        "• напоминания\n"
        "• идеи\n\n"
        "Сейчас я умею базово:\n"
        "• Любое сообщение = задача.\n"
        "• Сообщение, начинающееся с «идея:» или «idea:» = идея.\n\n"
        "Команды:\n"
        "/today — задачи (черновой режим)\n"
        "/tasks — все активные задачи\n"
        "/ideas — список идей\n"
    )


@dp.message(Command("today"))
async def cmd_today(message: Message):
    """Показывает активные задачи (потом доработаем фильтр по датам)."""
    tasks = db.get_active_tasks(message.from_user.id)
    if not tasks:
        await message.answer("На сегодня у тебя пока нет задач ✨")
        return

    lines = []
    for row in tasks:
        due_str = ""
        if row["due_at"]:
            due_str = f" (к {row['due_at']})"
        lines.append(f"• {row['text']}{due_str}")

    await message.answer("Твои активные задачи:\n" + "\n".join(lines))


@dp.message(Command("tasks"))
async def cmd_tasks(message: Message):
    """Все активные задачи пользователя."""
    tasks = db.get_active_tasks(message.from_user.id)
    if not tasks:
        await message.answer("У тебя нет активных задач ✅")
        return

    lines = []
    for row in tasks:
        due_str = ""
        if row["due_at"]:
            due_str = f" (к {row['due_at']})"
        lines.append(f"{row['id']}. {row['text']}{due_str}")

    await message.answer("Все активные задачи:\n" + "\n".join(lines))


@dp.message(Command("ideas"))
async def cmd_ideas(message: Message):
    """Показывает идеи пользователя."""
    notes = db.get_notes(message.from_user.id, note_type="idea")
    if not notes:
        await message.answer("Пока нет записанных идей 💡")
        return

    lines = []
    for row in notes:
        created = row["created_at"][:16].replace("T", " ")
        lines.append(f"{row['id']}. {row['text']} ({created} UTC)")

    await message.answer("Твои идеи:\n" + "\n".join(lines))


# --- Обработка обычных сообщений ---


@dp.message(F.text)
async def handle_text(message: Message):
    """
    Базовая логика:
    - если текст начинается с 'идея:' / 'idea:' → сохраняем как идею
    - иначе → сохраняем как задачу (без жёсткого дедлайна пока)
    """

    text = message.text.strip()

    # Идея
    lowered = text.lower()
    if lowered.startswith("идея:") or lowered.startswith("idea:"):
        clean_text = text.split(":", 1)[1].strip() if ":" in text else text
        note_id = db.add_note(message.from_user.id, clean_text, note_type="idea")
        await message.answer(f"Записал идею #{note_id}:\n«{clean_text}» 💡")
        return

    # Задача (простая версия, без парсинга даты)
    # Пока просто ставим дедлайн условно через 2 часа — дальше прикрутим LLM/парсинг.
    due_at = datetime.utcnow() + timedelta(hours=2)
    task_id = db.add_task(message.from_user.id, text, due_at=due_at)

    await message.answer(
        f"Записал задачу #{task_id}:\n«{text}»\n"
        f"Пока считаю дедлайн примерно через 2 часа.\n"
        "Позже научимся понимать дату/время прямо из текста."
    )


# --- Точка входа ---


async def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Не найден TELEGRAM_BOT_TOKEN в окружении (.env).")

    db.init_db()
    print("Бот запущен. Жду сообщения...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
