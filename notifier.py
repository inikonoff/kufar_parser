import logging
from typing import Dict, Any

from telegram import Bot
from telegram.constants import ParseMode

import config

logger = logging.getLogger(__name__)


async def notify_new_ad(bot: Bot, ad: Dict[str, Any]):
    """Отправляет сообщение о новом объявлении в Telegram."""
    text = _format_ad(ad)
    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление: {e}")


async def notify_missed_ads(bot: Bot, count: int):
    """Сообщение о пропущенных объявлениях после Стопа."""
    category_url = (
        f"https://www.kufar.by/category/{config.KUFAR_CATEGORY_ID}"
    )
    text = (
        f"📦 Пока слежка была приостановлена, появилось <b>{count}</b> "
        f"новых объявлений.\n\n"
        f'<a href="{category_url}">Посмотреть на kufar.by →</a>'
    )
    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение о пропущенных: {e}")


def _format_ad(ad: Dict[str, Any]) -> str:
    """Форматирует объявление в текст для Telegram."""
    title = ad.get("title", "Без названия")
    price = ad.get("price", "Цена не указана")
    url = ad.get("url", "")

    return (
        f"🆕 <b>{title}</b>\n"
        f"💰 {price}\n\n"
        f'<a href="{url}">Открыть объявление →</a>'
    )
