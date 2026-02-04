import aiohttp
import logging
from typing import List, Dict, Any

import config

logger = logging.getLogger(__name__)

# Реальный API эндпоинт kufar.by
KUFAR_API_URL = "https://api.kufar.by/search-api/v2/search/rendered-paginated"

# Заголовки — имитируем обычный браузер
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.kufar.by/",
    "Origin": "https://www.kufar.by",
}


async def fetch_ads(category_id: int = None) -> List[Dict[str, Any]]:
    """
    Тянет список объявлений с kufar.by для указанной категории.
    Возвращает список словарей с полями:
        id, title, price, url
    """
    if category_id is None:
        category_id = config.KUFAR_CATEGORY_ID

    params = {
        "cat": category_id,
        "lang": "ru",
        "size": 50,
        "sort": "lst.d",  # lst.d = сортировка по дате, новые первыми
    }

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(KUFAR_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    logger.warning(f"Kufar ответил со статусом {resp.status}")
                    return []

                data = await resp.json(content_type=None)
                logger.debug(f"Получен ответ от Kufar: {len(data.get('ads', []))} объявлений")
                return _parse_response(data)

    except aiohttp.ClientError as e:
        logger.error(f"Ошибка запроса к kufar: {e}")
        return []
    except Exception as e:
        logger.error(f"Неизвестная ошибка парсера: {e}")
        return []


def _parse_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Парсит ответ API kufar и вытаскивает нужные поля.
    Структура ответа может измениться — тут основная точка адаптации.
    """
    ads = []
    items = data.get("ads", [])

    for item in items:
        ad_id = item.get("ad_id")
        if not ad_id:
            continue

        title = item.get("subject", "Без названия")
        price = _format_price(item.get("price_byn"), item.get("price_usd"))
        url = f"https://www.kufar.by/item/{ad_id}"

        ads.append({
            "id": ad_id,
            "title": title,
            "price": price,
            "url": url,
        })

    return ads


def _format_price(price_byn, price_usd) -> str:
    """Форматирует цену в читаемую строку."""
    if price_byn and price_byn != "0":
        return f"{float(price_byn):,.0f} Br".replace(",", " ")
    
    if price_usd and price_usd != "0":
        return f"{float(price_usd):,.0f} $".replace(",", " ")
    
    return "Цена не указана"
