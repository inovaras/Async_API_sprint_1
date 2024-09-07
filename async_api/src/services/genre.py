from functools import lru_cache
from typing import List, Optional

from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.genre import Genre
from redis.asyncio import Redis

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_genres(
        self, index: str, per_page: int, offset: int
    ) -> List[Genre]:
        """Получить список жанров с пагинацией.
        Данная реализация ограничена 10000 результатов и страдает от глубокой пагинации.
        См. статью ниже - в ней описаны различные варианты пагинации и проблемы связанные с ними.
        https://opster.com/guides/elasticsearch/how-tos/elasticsearch-pagination-techniques/
        Args:
            index (str): индекс жанров в elasticsearch.
            per_page (int): количество жанров на страницу.
            offset (int): сдиг жанров при переходе на следующую страницу.

        Returns:
            list(genre): список жанров.
        """
        # TODO add cache redis
        data = await self.elastic.search(
            index=index,
            size=per_page,
            from_=offset,
        )
        genres = []
        for doc in data.body["hits"]["hits"]:
            genres.append(Genre(**doc["_source"]))

        return genres

    # get_by_id возвращает объект жанра. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        genre = await self._genre_from_cache(genre_id)
        if not genre:
            # Если жанра нет в кеше, то ищем его в Elasticsearch
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_genre_to_cache(genre)

        return genre

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        """Получить один жанр из elasticsearch.

        если вам нужно вхождение полной фразы - используйте match_phrase.

        Args:
            genre_id (str): id жанра.

        Returns:
            Optional[Genre]: вернет жанр или None.
        """
        try:
            doc = await self.elastic.get(index="genres", id=genre_id)
        except NotFoundError:
            return None

        return Genre(**doc["_source"])


    async def _genre_from_cache(self, genre_id: str) -> Optional[Genre]:
        """Взять жанр из кэша.

        Args:
            genre_id (str): id жанра.

        Returns:
            Optional[Genre]: вернет жанр или None.
        """
        # Пытаемся получить данные о жанре из кеша, используя команду get
        # https://redis.io/commands/get/
        data = await self.redis.get(genre_id)
        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        genre = Genre.model_validate_json(data)
        return genre

    async def _put_genre_to_cache(self, genre: Genre):
        """Положить жанр в кэш.

        Args:
            genre (Genre): id жанра.
        """
        # Сохраняем данные о жанре, используя команду set
        # Выставляем время жизни кеша — 5 минут
        # https://redis.io/commands/set/
        # pydantic позволяет сериализовать модель в json
        await self.redis.set(genre.id, genre.model_dump_json(), FILM_CACHE_EXPIRE_IN_SECONDS)


    async def _get_genre_by_name_from_elastic(self, genre_name: str) -> Optional[Genre]:
        """Получить один жанр из elasticsearch.

        если вам нужно вхождение полной фразы - используйте match_phrase.

        Args:
            genre_name (str): название жанра.

        Returns:
            Optional[Genre]: вернет жанр или None.
        """
        data = await self.elastic.search(
            index="genres",
            query={"match": {"name": genre_name}},  # нечеткий поиск по нескольким словам
        )
        for doc in data.body["hits"]["hits"]:
            if doc:
                return Genre(**doc["_source"])
            return None



# TODO включить lru_cache() правильно, тк работает и без него
@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
