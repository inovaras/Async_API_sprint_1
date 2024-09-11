from functools import lru_cache

from core.config import settings
from db.elastic import get_elastic
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from models.person import Person

from services.base import BaseService
from state.state import State, get_storage


class PersonService(BaseService):

    def __init__(self, state: State, elastic: AsyncElasticsearch):
        super().__init__(state, elastic)
        self.index = "persons"
        self.expire = settings.PERSON_CACHE_EXPIRE_IN_SECONDS
        self.model = Person


@lru_cache()
def get_person_service(
    state: State = Depends(get_storage),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> BaseService:
    return PersonService(state, elastic)


