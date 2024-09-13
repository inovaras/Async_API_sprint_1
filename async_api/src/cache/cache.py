import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from db.redis import get_redis
from redis.asyncio import Redis


class BaseCacheStorage(ABC):
    """Абстрактное хранилище кэша.

    Позволяет сохранять и получать кэш.
    Способ хранения кэша может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abstractmethod
    def save_cache(self, key: str, cache: Dict[str, Any], expire: int | None = None) -> None:
        """Сохранить кэш в хранилище."""

    @abstractmethod
    def retrieve_cache(self, key: str) -> Dict[str, Any]:
        """Получить кэш из хранилища."""


class RedisCacheStorage(BaseCacheStorage):

    def __init__(self, redis_adapter: Redis) -> None:
        self.redis_adapter = redis_adapter

    async def save_cache(self, key: str, cache: Dict[str, Any], expire: int | None = None) -> None:
        """Сохранить кэш в хранилище."""
        await self.redis_adapter.set(key, cache, ex=expire)

    async def retrieve_cache(self, key) -> Dict[str, Any]:
        """Получить кэш из хранилища."""
        cache = await self.redis_adapter.get(key)
        logging.debug(cache)
        return cache


class Cache:
    """Класс для работы с кэшэм."""

    def __init__(self, storage: BaseCacheStorage) -> None:
        self.storage = storage

    async def set_cache(self, key: str, value: Any, expire: int | None = None) -> None:
        """Установить кэш для определённого ключа."""
        await self.storage.save_cache(key, value, expire)

    async def get_cache(self, key: str) -> Any:
        """Получить кэш по определённому ключу."""
        cache = await self.storage.retrieve_cache(key)
        if cache is None:
            return None

        return cache


async def get_cache_storage():
    redis = await get_redis()
    storage = RedisCacheStorage(redis_adapter=redis)

    return Cache(storage=storage)
