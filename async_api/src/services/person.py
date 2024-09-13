from functools import lru_cache

from cache.cache import Cache, get_cache_storage
from core.config import settings
from db.elastic import get_elastic
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from models.person import Person
from services.base import BaseService


class PersonService(BaseService):

    def __init__(self, cache: Cache, elastic: AsyncElasticsearch):
        super().__init__(cache, elastic)
        self.index = "persons"
        self.expire = settings.PERSON_CACHE_EXPIRE_IN_SECONDS
        self.model = Person


@lru_cache()
def get_person_service(
    cache: Cache = Depends(get_cache_storage),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> BaseService:
    return PersonService(cache, elastic)
