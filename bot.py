import logging

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

import config
from state import BotState
from notifier import notify_missed_ads
import parser as kufar_parser

logger = logging.getLogger(__name__)

# ─── Кнопки ─────────────────────────────────────────────────────────────────

KB_MAIN_INACTIVE = ReplyKeyboardMarkup(
    [["▶️ Старт"], ["☰ Меню"]],
    resize_keyboard=True,
)

KB_MAIN_ACTIVE = ReplyKeyboardMarkup(
    [["⏹️ Стоп"], ["☰ Меню"]],
    resize_keyboard=True,
)

KB_MENU = ReplyKeyboardMarkup(
    [["🔄 Перезапустить"], ["⬅️ Назад"]],
    resize_keyboard=True,
)

# ─── Имя категории для текстов ──────────────────────────────────────────────

CATEGORY_NAMES = {
    5070: "Фототехника и оптика",
    5000: "Техника",
    5010: "Телефоны",
    5020: "Аудиотехника",
    5030: "Компьютеры и комплектующие",
    5040: "Игры и приставки",
    5050: "Оргтехника",
    5060: "ТВ и видеотехника",
    5080: "Планшеты и электронные книги",
    5090: "Бытовая техника",
    1000: "Недвижимость",
    2000: "Авто и транспорт",
    2010: "Легковые авто",
    3000: "Все для дома",
    4000: "Хобби, спорт и туризм",
    6000: "Работа, бизнес, учёба",
    7000: "Прочее",
    8000: "Мода и стиль",
    9000: "Свадьба и праздники",
    10000: "Сад и огород",
    11000: "Животные",
    12000: "Всё для детей и мам",
    13000: "Услуги",
    14000: "Ремонт и стройка",
}


def get_category_name() -> str:
    return CATEGORY_NAMES.get(config.KUFAR_CATEGORY_ID, f"Категория {config.KUFAR_CATEGORY_ID}")


def get_keyboard(state: BotState) -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру в зависимости от текущего состояния."""
    if state.status == "active":
        return KB_MAIN_ACTIVE
    return KB_MAIN_INACTIVE


# ─── Обработчики ────────────────────────────────────────────────────────────

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — приветствие."""
    state = context.bot_data["state"]
    category = get_category_name()

    # Если бот уже активен — просто напомнить
    if state.status == "active":
        await update.message.reply_text(
            f"👋 Слежка уже активна за категорией <b>{category}</b>.",
            parse_mode="HTML",
            reply_markup=KB_MAIN_ACTIVE,
        )
        return

    await update.message.reply_text(
        f"👋 Привет! Я отслеживаю новые объявления на kufar.by.\n\n"
        f"Категория: <b>{category}</b>\n\n"
        f"Нажми <b>Старт</b>, чтобы начать.",
        parse_mode="HTML",
        reply_markup=KB_MAIN_INACTIVE,
    )


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общий обработчик текстовых кнопок."""
    text = update.message.text
    state: BotState = context.bot_data["state"]

    if text == "▶️ Старт":
        await _start_scan(update, context, state)
    elif text == "⏹️ Стоп":
        await _stop_scan(update, context, state)
    elif text == "☰ Меню":
        await _show_menu(update, context)
    elif text == "🔄 Перезапустить":
        await _restart_scan(update, context, state)
    elif text == "⬅️ Назад":
        await _back(update, context, state)
    else:
        # Неизвестная кнопка — просто показываем текущую клавиатуру
        await update.message.reply_text(
            "Используй кнопки ниже.",
            reply_markup=get_keyboard(state),
        )


# ─── Внутренние функции кнопок ──────────────────────────────────────────────

async def _start_scan(update: Update, context: ContextTypes.DEFAULT_TYPE, state: BotState):
    """Кнопка Старт."""
    bot = context.bot
    category = get_category_name()

    # Если был Стоп — считаем пропущенные объявления
    if state.status == "stopped" and state.stopped_at:
        missed = await _count_missed(state)
        if missed > 0:
            await notify_missed_ads(bot, missed)

    # Переключаем в active
    state.set_active()

    await update.message.reply_text(
        f"✅ Ожидаю публикацию объявлений в категории <b>{category}</b>. "
        f"О появлении будет сообщено.",
        parse_mode="HTML",
        reply_markup=KB_MAIN_ACTIVE,
    )


async def _stop_scan(update: Update, context: ContextTypes.DEFAULT_TYPE, state: BotState):
    """Кнопка Стоп."""
    state.set_stopped()

    await update.message.reply_text(
        "⏹️ Слежка приостановлена.",
        reply_markup=KB_MAIN_INACTIVE,
    )


async def _show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка Меню."""
    await update.message.reply_text(
        "☰ Меню",
        reply_markup=KB_MENU,
    )


async def _restart_scan(update: Update, context: ContextTypes.DEFAULT_TYPE, state: BotState):
    """Кнопка Перезапустить — полный сброс."""
    state.set_reset()
    category = get_category_name()

    await update.message.reply_text(
        f"🔄 Бот сброшен. Нажми <b>Старт</b>, чтобы возобновить слежку за <b>{category}</b>.",
        parse_mode="HTML",
        reply_markup=KB_MAIN_INACTIVE,
    )


async def _back(update: Update, context: ContextTypes.DEFAULT_TYPE, state: BotState):
    """Кнопка Назад — возвращаем на главный экран."""
    await update.message.reply_text(
        "Главное меню",
        reply_markup=get_keyboard(state),
    )


# ─── Подсчёт пропущенных ────────────────────────────────────────────────────

async def _count_missed(state: BotState) -> int:
    """
    Тянем текущие объявления и считаем, сколько из них юзер ещё не видел.
    Это лёгкий запрос — просто один fetch при Старте.
    """
    ads = await kufar_parser.fetch_ads()
    missed = sum(1 for ad in ads if not state.is_seen(ad["id"]))
    return missed
