import asyncio
import logging
import random

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import config
from state import BotState
from bot import handle_start, handle_button
from notifier import notify_new_ad
import parser as kufar_parser

# ─── Логирование ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Цикл сканирования ──────────────────────────────────────────────────────

async def scan_loop(app):
    """
    Бесконечный цикл парсинга.
    Работает только когда state == active.
    Интервал между запросами — случайное число от SCAN_INTERVAL_MIN до SCAN_INTERVAL_MAX.
    """
    state: BotState = app.bot_data["state"]

    while True:
        interval = random.randint(config.SCAN_INTERVAL_MIN, config.SCAN_INTERVAL_MAX)

        if state.status == "active":
            try:
                ads = await kufar_parser.fetch_ads()

                for ad in ads:
                    if not state.is_seen(ad["id"]):
                        # Новое объявление — уведомляем и запоминаем
                        state.add_seen(ad["id"])
                        await notify_new_ad(app.bot, ad)
                        logger.info(f"Новое объявление: {ad['id']} — {ad['title']}")

            except Exception as e:
                logger.error(f"Ошибка в цикле сканирования: {e}")
        else:
            logger.debug(f"Слежка неактивна (status={state.status}), пропускаем.")

        logger.debug(f"Следующий скан через {interval}с")
        await asyncio.sleep(interval)


# ─── Старт приложения ───────────────────────────────────────────────────────

async def main():
    config.validate()

    # Инициализация состояния
    state = BotState()

    # Собираем Telegram-бот
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.bot_data["state"] = state

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button))

    # Стартуем цикл сканирования в фоне
    async with app:
        asyncio.create_task(scan_loop(app))
        logger.info("Бот запущен. Ожидаю команды.")
        # Держим процесс живым
        await asyncio.Event().wait()


# ─── Точка входа ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(main())
