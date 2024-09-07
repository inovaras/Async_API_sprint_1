import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

from core import config
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.film import Film
from models.genre import Genre
from models.person import Person
from pydantic import BaseModel
from redis.asyncio import Redis


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def _get_object_from_cache(self, key: str, model: BaseModel) -> Optional[BaseModel]:
        """Взять данные из кэша, сохраненные по ключу.

        Args:
            key (str): ключ для поиска в redis.

        Returns:
            Optional[BaseModel]: вернет pydantic model или None.
        """
        data = await self.redis.get(key)
        if not data:
            return None

        pydantic_model = model.model_validate_json(data)
        return pydantic_model

    async def _get_objects_from_cache(self, key: str, model: BaseModel) -> Optional[List[BaseModel]]:
        """Взять данные из кэша, сохраненные по ключу.

        Args:
            key (str): ключ для поиска в redis.

        Returns:
            Optional[List[BaseModel]]: None или список c данными в формате pydantic models, унаследованных от BaseModel.
        """
        data = await self.redis.get(key.lower())
        if not data:
            return None

        models = [model.model_validate_json(entity) for entity in json.loads(data)]

        return models

    async def _put_object_to_cache(self, data: BaseModel, expire: int):
        """Положить данные pydantic model в кэш.

        Args:
            data (BaseModel): данные pydantic model, например данные Person.
            expire (int): срок хранения данных в кэше, в секундах.
        """
        await self.redis.set(data.id, data.model_dump_json(), expire)

    async def _put_objects_to_cache(self, key: str, models: List[BaseModel], expire: int):
        """Положить данные в кэш.

        Args:
            key (str): ключ под которым будут сохранены данные в redis.
            models (List[BaseModel]): список данных в формате моделей, унаследованных от BaseModel.
            expire (int): срок хранения данных в кэше, в секундах.
        """
        data = []
        for model in models:
            data.append(model.model_dump_json())

        await self.redis.set(key.lower(), json.dumps(data), expire)

    async def _get_from_elastic(self, id_: str, index: str, model: BaseModel) -> Optional[BaseModel]:
        """Получить одну персону из elasticsearch.

        Args:
            id_ (str): id в elascticsearch.

        Returns:
            Optional[BaseModel]: вернет персону или None.
        """
        try:
            doc = await self.elastic.get(id=id_, index=index)
        except NotFoundError:
            return None
        return model(**doc["_source"])

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
            # query={"match": {"name": genre_name}},
            query={"match_phrase": {"name": {"query": genre_name}}},
        )
        for doc in data.body["hits"]["hits"]:
            if doc:
                return Genre(**doc["_source"])
            return None


    # get_film_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_film_by_id(self, film_id: str) -> Optional[Film]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self._get_object_from_cache(key=film_id, model=Film)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_from_elastic(id_=film_id, index="movies", model=Film)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_object_to_cache(data=film, expire=config.FILM_CACHE_EXPIRE_IN_SECONDS)

        return film


    async def get_person_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._get_object_from_cache(key=person_id, model=Person)
        if not person:
            person = await self._get_from_elastic(id_=person_id, index="persons", model=Person)
            if not person:
                return None

            await self._put_object_to_cache(person, expire=config.PERSON_CACHE_EXPIRE_IN_SECONDS)

        return person


    async def get_genre_by_id(self, genre_id: str) -> Optional[Genre]:
        genre = await self._get_object_from_cache(key=genre_id, model=Genre)
        if not genre:
            genre = await self._get_from_elastic(id_=genre_id, index="genres", model=Genre)
            if not genre:
                return None

            await self._put_object_to_cache(data=genre, expire=config.GENRE_CACHE_EXPIRE_IN_SECONDS)

        return genre

    async def get_genre_by_name(self, genre_name: str) -> Optional[BaseModel]:
        genre = await self._get_object_from_cache(key=genre_name, model=Genre)
        if not genre:
            genre = await self._get_genre_by_name_from_elastic(genre_name)
            if not genre:
                return None

            await self._put_object_to_cache(data=genre, expire=config.GENRE_CACHE_EXPIRE_IN_SECONDS)

        return genre

    # INFO OK
    async def get_objects(
        self,
        index: str,
        per_page: int,
        offset: int,
        sort: List[dict] | None,
        search_query: Dict[str, Any] | None,
        cache_key: str,
        model: BaseModel,
        expire: int,
    ) -> Optional[List[BaseModel]]:
        """Получить список персон с пагинацией.
        Данная реализация ограничена 10000 результатов и страдает от глубокой пагинации.
        См. статью ниже - в ней описаны различные варианты пагинации и проблемы связанные с ними.
        https://opster.com/guides/elasticsearch/how-tos/elasticsearch-pagination-techniques/
        Args:
            index (str): индекс в elasticsearch.
            per_page (int): количество фильмов на страницу.
            offset (int): сдвиг при переходе на следующую страницу.
            sort (list(dict)): запрос сортировки в elastichsearch.
            persons_filter (List[Dict[str, Any]]): запрос фильтрации в elasticsearch.

        Returns:
            list(Person): список персон.
        """
        # search in redis
        objects = await self._get_objects_from_cache(key=cache_key, model=model)
        if not objects:
            data = await self.elastic.search(
                index=index,
                size=per_page,
                from_=offset,
                sort=sort,
                query=search_query,
            )
            objects = []
            for doc in data.body["hits"]["hits"]:
                objects.append(model(**doc["_source"]))
            if not objects:
                return None
            # save in redis
            await self._put_objects_to_cache(key=cache_key, models=objects, expire=expire)

        return objects


# TODO включить lru_cache() правильно, тк работает и без него
@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
