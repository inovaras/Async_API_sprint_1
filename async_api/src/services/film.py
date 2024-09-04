from functools import lru_cache
from typing import Any, Dict, List, Optional

from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.film import Film
from models.genre import Genre
from models.person import Person
from redis.asyncio import Redis

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут

from elasticsearch.helpers import scan


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_films(
        self, index: str, per_page: int, offset: int, sort: List[dict] | None, films_filter: Dict[str, Any] | None
    ) -> List[Film]:
        """Получить список фильмов с пагинацией.
        Данная реализация ограничена 10000 результатов и страдает от глубокой пагинации.
        См. статью ниже - в ней описаны различные варианты пагинации и проблемы связанные с ними.
        https://opster.com/guides/elasticsearch/how-tos/elasticsearch-pagination-techniques/
        Args:
            index (str): индекс фильмов в elasticsearch.
            per_page (int): количество фильмов на страницу.
            offset (int): сдиг фильмов при переходе на следующую страницу.
            sort (list(dict)): запрос сортировки в elastichsearch.
            films_filter (List[Dict[str, Any]]): запрос фильтрации в elasticsearch.

        Returns:
            list(Film): список фильмов.
        """
        # TODO add cache redis
        data = await self.elastic.search(
            index=index,
            size=per_page,
            from_=offset,
            sort=sort,
            query=films_filter,  # нечеткий поиск по нескольким словам
        )
        films = []
        for doc in data.body["hits"]["hits"]:
            films.append(Film(**doc["_source"]))

        return films

    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self._film_from_cache(film_id)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_id)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        """Получить один фильм из elasticsearch.

        Args:
            film_id (str): id фильма.

        Returns:
            Optional[Film]: вернет фильм или None.
        """
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return Film(**doc["_source"])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        """Взять фильм из кэша.

        Args:
            film_id (str): id фильма.

        Returns:
            Optional[Film]: вернет фильм или None.
        """
        # Пытаемся получить данные о фильме из кеша, используя команду get
        # https://redis.io/commands/get/
        data = await self.redis.get(film_id)
        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        film = Film.model_validate_json(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        """Положить фильм в кэш.

        Args:
            film (Film): id фильма.
        """
        # Сохраняем данные о фильме, используя команду set
        # Выставляем время жизни кеша — 5 минут
        # https://redis.io/commands/set/
        # pydantic позволяет сериализовать модель в json
        await self.redis.set(film.id, film.model_dump_json(), FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        """Получить один жанр из elasticsearch.

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

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        """Получить одну персону из elasticsearch.

        Args:
            person_id (str): id персоны.

        Returns:
            Optional[Genre]: вернет персону или None.
        """
        try:
            doc = await self.elastic.get(index="persons", id=person_id)
        except NotFoundError:
            return None
        return Person(**doc["_source"])


# TODO включить lru_cache() правильно, тк работает и без него
@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
