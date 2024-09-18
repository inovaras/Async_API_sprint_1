import json
from abc import ABC
from typing import List, Optional

from cache.cache import Cache
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Request
from fastapi.datastructures import URL
from pydantic import BaseModel
from utils.utils import get_pagination_params


class BaseService(ABC):
    """Абстрактный класс, реализующий базоый функционал сервиса.

    Используется только через наследование.
    В классе-наследнике необходимо указать index, expire, model.
    index (str) - индекс для поиска в elasticsearch. Пример: "genres".
    expire (int) - срок хранения в кэше, в секундах. Пример: 300.
    model (BaseModel) - pydantic модель используемая в сервисе. Пример: Film, Genre, Person.
    """

    def __init__(self, cache: Cache, elastic: AsyncElasticsearch):
        self.cache = cache
        self.elastic = elastic
        self.index = ""
        self.expire = 0
        self.model: BaseModel = None

    async def _get_from_cache(self, key: str) -> Optional[BaseModel | List[BaseModel]]:
        data = await self.cache.get_cache(key)
        if not data:
            return None

        validate_data = json.loads(data)
        if isinstance(validate_data, list):
            cache = [self.model.model_validate_json(entity) for entity in validate_data]
        else:
            cache = self.model.model_validate_json(data)

        return cache

    async def _put_to_cache(self, key: str, data: BaseModel | List[BaseModel]):
        """Положить данные в кэш.

        expire (int): срок хранения данных в кэше, в секундах. Указывается в классе-наследнике.
        """
        if isinstance(data, BaseModel):
            await self.cache.set_cache(key, data.model_dump_json(), self.expire)
        elif isinstance(data, list):
            cache = []
            for obj in data:
                cache.append(obj.model_dump_json())
            await self.cache.set_cache(key.lower(), json.dumps(cache), self.expire)

    async def _get_from_elastic(self, id_: str) -> Optional[BaseModel]:
        try:
            doc = await self.elastic.get(id=id_, index=self.index)
        except NotFoundError:
            return None
        return self.model(**doc["_source"])

    async def get_by_id(self, id_: str) -> Optional[BaseModel]:
        """Обертка для запросов в кэш и хранилище."""
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        model = await self._get_from_cache(key=id_)
        if not model:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            model = await self._get_from_elastic(id_=id_)
            if not model:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_to_cache(key=id_, data=model)

        return model

    async def _get_correct_params(self, query_params: dict) -> dict:
        if query_params:
            for param in query_params.items():
                key, value = param
                if value:
                    if value.isdigit():
                        value = int(value)
                    query_params[key] = value

        if not query_params.get("page"):
            pagination = get_pagination_params()
            query_params.update(
                {"page": pagination["page"].get_default()}
            )

        if not query_params.get("per_page"):
            pagination = get_pagination_params()
            query_params.update(
                {"per_page": pagination["per_page"].get_default()}
            )

        sort = query_params.get('sort_by')
        query_params['sort'] = []
        if sort == 'imdb_rating' or sort == '-imdb_rating':
            if query_params["sort_by"] == "-imdb_rating":
                query_params["sort"].append({"imdb_rating": "desc"})
            elif query_params["sort_by"] == "imdb_rating":
                query_params["sort"].append({"imdb_rating": "asc"})
        elif not sort:
            query_params['sort'] = [{"_score": "desc"}]

        query_params["offset"] = (query_params["page"] - 1) * query_params["per_page"]

        return query_params

    async def _get_cache_key(self, url: URL) -> str:
        return f"{url.path}?{url.query}"

    async def _build_query_request(self, params: dict, url: URL, path_params: dict) -> dict:
        """Сформировать поисковый запрос для elasticsearch.

        params - параметры, которые идут после знака "?". Пример: /api/v1/person?sort=imdb_rating&page=1
        path_params - параметры, которые подставляются в path. Пример: /api/v1/person/{id}
        """
        search_query = None
        filter_by = params.get("filter_by")
        query = params.get("query")
        genre_name = params.get("genre")

        # если есть параметры пути значит это запросы с .../{id}/...
        if path_params:
            person_id = path_params.get('person_id')
            if f"/api/v1/persons/{person_id}/film" in url.path:
                search_query = {
                    "bool": {
                        "should": [
                            {"nested": {"path": "directors", "query": {"term": {"directors.id": person_id}}}},
                            {"nested": {"path": "writers", "query": {"term": {"writers.id": person_id}}}},
                            {"nested": {"path": "actors", "query": {"term": {"actors.id": person_id}}}},
                        ]
                    }
                }

        if url.path == "/api/v1/films":
            if filter_by == "imdb_rating":
                search_query = {"term": {filter_by: query}}
            elif filter_by == "genre" and genre_name:
                search_query = {"match": {"genres": genre_name}}
            elif filter_by in ["title", "description"]:
                search_query = {"match_phrase": {filter_by: {"query": query}}}
            elif filter_by in ["actors", "directors", "writers"]:
                search_query = {
                    "bool": {
                        "must": [
                            {
                                "nested": {
                                    "path": filter_by,
                                    "query": {
                                        "bool": {"must": [{"match_phrase": {f"{filter_by}.name": {"query": query}}}]}
                                    },
                                }
                            },
                        ]
                    }
                }
        elif url.path == "/api/v1/films/search":
            search_query = {
                "multi_match": {
                    "query": query,
                    # "fuzziness": "2",
                    "fields": ["title", "description"],
                }
            }
        elif url.path == "/api/v1/genres":
            search_query = None
        elif url.path == "/api/v1/persons/search":
            search_query = {"match_phrase": {"full_name": {"query": query}}}
        elif "/api/v1/persons/" in url.path and "film" in url.path:
            person_id = params.get("person_id")

        return search_query

    async def get_objects(self, request: Request) -> Optional[List[BaseModel]]:
        """Получить список персон с пагинацией.
        Данная реализация ограничена 10000 результатов и страдает от глубокой пагинации.
        См. статью ниже - в ней описаны различные варианты пагинации и проблемы связанные с ними.
        https://opster.com/guides/elasticsearch/how-tos/elasticsearch-pagination-techniques/

        index для поиска указывается в классе-наследнике абстрактного сервиса.\n
        Параметры для поиска достаются из request.

        Args:
            request (Request): инстанс запроса FastApi.
        """
        url = request.url
        # INFO использовать _dict для query_params т.к. обновляю словарь на лету.
        query_params = request.query_params._dict
        path_params = request.path_params
        params = await self._get_correct_params(query_params)
        cache_key = await self._get_cache_key(url)

        objects = await self._get_from_cache(key=cache_key)
        if not objects:
            search_query = await self._build_query_request(params=params, url=url, path_params=path_params)
            data = await self.elastic.search(
                index=self.index,
                size=params["per_page"],
                from_=params["offset"],
                sort=params["sort"],
                query=search_query,
            )
            objects = []
            for doc in data.body["hits"]["hits"]:
                objects.append(self.model(**doc["_source"]))
            if not objects:
                return None

            await self._put_to_cache(key=cache_key, data=objects)

        return objects
