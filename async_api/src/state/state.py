import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from db.redis import get_redis
from redis.asyncio import Redis


class BaseStorage(ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abstractmethod
    def save_state(self, key: str, state: Dict[str, Any], expire: int | None = None) -> None:
        """Сохранить состояние в хранилище."""

    @abstractmethod
    def retrieve_state(self, key: str) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class RedisStorage(BaseStorage):

    def __init__(self, redis_adapter: Redis) -> None:
        self.redis_adapter = redis_adapter

    async def save_state(self, key: str, state: Dict[str, Any], expire: int | None = None) -> None:
        """Сохранить состояние в хранилище."""
        await self.redis_adapter.set(key, state, ex=expire)

    async def retrieve_state(self, key) -> Dict[str, Any]:
        """Получить состояние из хранилища."""
        state = await self.redis_adapter.get(key)
        logging.debug(state)
        return state


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    async def set_state(self, key: str, value: Any, expire: int | None = None) -> None:
        """Установить состояние для определённого ключа."""
        await self.storage.save_state(key, value, expire)

    async def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        state = await self.storage.retrieve_state(key)
        if state is None:
            return None

        return state


async def get_storage():
    redis = await get_redis()
    storage = RedisStorage(redis_adapter=redis)

    return State(storage=storage)
