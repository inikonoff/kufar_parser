import json
import os
from datetime import datetime, timezone
from typing import Optional

import config


class BotState:
    """
    Состояния бота:
        active   — слежка идёт
        stopped  — слежка приостановлена (есть дата остановки)
        reset    — сброшен (как свежий старт, без истории)
    """

    def __init__(self):
        self._state = {
            "status": "reset",           # active | stopped | reset
            "stopped_at": None,          # ISO timestamp момента Стопа
            "seen_ids": [],              # список виденных ID объявлений
        }
        self._load()

    # ─── Загрузка / сохранение ──────────────────────────────────────────

    def _load(self):
        if os.path.exists(config.STATE_FILE):
            try:
                with open(config.STATE_FILE, "r") as f:
                    self._state = json.load(f)
            except (json.JSONDecodeError, KeyError):
                # Если файл повреждён — стартуем заново
                self._state = {"status": "reset", "stopped_at": None, "seen_ids": []}
                self.save()

    def save(self):
        with open(config.STATE_FILE, "w") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    # ─── Статус ─────────────────────────────────────────────────────────

    @property
    def status(self) -> str:
        return self._state["status"]

    def set_active(self):
        self._state["status"] = "active"
        self._state["stopped_at"] = None
        self.save()

    def set_stopped(self):
        self._state["status"] = "stopped"
        self._state["stopped_at"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def set_reset(self):
        self._state["status"] = "reset"
        self._state["stopped_at"] = None
        self._state["seen_ids"] = []
        self.save()

    # ─── Seen IDs ───────────────────────────────────────────────────────

    def is_seen(self, ad_id: int) -> bool:
        return ad_id in self._state["seen_ids"]

    def add_seen(self, ad_id: int):
        if ad_id not in self._state["seen_ids"]:
            self._state["seen_ids"].append(ad_id)
            # Режим скольжащего окна — убираем старые ID
            if len(self._state["seen_ids"]) > config.SEEN_IDS_LIMIT:
                self._state["seen_ids"] = self._state["seen_ids"][-config.SEEN_IDS_LIMIT:]
            self.save()

    # ─── Дата остановки ─────────────────────────────────────────────────

    @property
    def stopped_at(self) -> Optional[datetime]:
        if self._state["stopped_at"]:
            return datetime.fromisoformat(self._state["stopped_at"])
        return None
