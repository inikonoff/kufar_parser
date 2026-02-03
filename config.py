import os

# Telegram
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: int = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Kufar
KUFAR_CATEGORY_ID: int = int(os.getenv("KUFAR_CATEGORY_ID", "5070"))  # Фототехника и оптика

# Интервалы сканирования (секунды)
SCAN_INTERVAL_MIN: int = int(os.getenv("SCAN_INTERVAL_MIN", "41"))
SCAN_INTERVAL_MAX: int = int(os.getenv("SCAN_INTERVAL_MAX", "94"))

# Файл состояния на диске
STATE_FILE: str = "state.json"

# Сколько последних виденных ID хранить в памяти (чтобы файл не рос бесконечно)
SEEN_IDS_LIMIT: int = 500


def validate():
    """Проверяем обязательные переменные при старте."""
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN не установлена")
    if TELEGRAM_CHAT_ID == 0:
        errors.append("TELEGRAM_CHAT_ID не установлена")
    if SCAN_INTERVAL_MIN >= SCAN_INTERVAL_MAX:
        errors.append("SCAN_INTERVAL_MIN должен быть меньше SCAN_INTERVAL_MAX")
    if errors:
        raise ValueError("Ошибки конфигурации:\n" + "\n".join(f"  • {e}" for e in errors))
