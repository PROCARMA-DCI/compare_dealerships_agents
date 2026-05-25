import asyncio
import copy
from uuid import uuid4


class InMemoryChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_settings = None
        self._items: list[dict] = []
        self._lock = asyncio.Lock()

    async def get_items(self, limit: int | None = None) -> list[dict]:
        async with self._lock:
            items = self._items if limit is None else self._items[-limit:]
            return copy.deepcopy(items)

    async def add_items(self, items: list[dict]) -> None:
        async with self._lock:
            self._items.extend(copy.deepcopy(items))

    async def pop_item(self) -> dict | None:
        async with self._lock:
            if not self._items:
                return None
            return copy.deepcopy(self._items.pop())

    async def clear_session(self) -> None:
        async with self._lock:
            self._items.clear()


_sessions: dict[str, InMemoryChatSession] = {}
_sessions_lock = asyncio.Lock()


async def get_or_create_chat_session(session_id: str | None = None) -> InMemoryChatSession:
    if not session_id:
        session_id = str(uuid4())

    async with _sessions_lock:
        session = _sessions.get(session_id)
        if session is None:
            session = InMemoryChatSession(session_id)
            _sessions[session_id] = session
        return session


async def clear_chat_session(session_id: str) -> bool:
    async with _sessions_lock:
        session = _sessions.pop(session_id, None)

    if session is None:
        return False

    await session.clear_session()
    return True
