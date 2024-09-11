from functools import lru_cache
from typing import Optional

from core.config import settings
from db.elastic import get_elastic
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from models.genre import Genre
from pydantic import BaseModel

from services.base import BaseService
from state.state import State, get_storage


class GenreService(BaseService):

    def __init__(self, state: State, elastic: AsyncElasticsearch):
        super().__init__(state, elastic)
        self.index = "genres"
        self.expire = settings.GENRE_CACHE_EXPIRE_IN_SECONDS
        self.model = Genre

    async def _get_genre_by_name_from_elastic(self, genre_name: str) -> Optional[Genre]:
        """Получить один жанр из elasticsearch.

        если вам нужно вхождение полной фразы - используйте match_phrase.

        Args:
            genre_name (str): название жанра.

        Returns:
            Optional[Genre]: вернет жанр или None.
        """
        # TODO add cache
        data = await self.elastic.search(
            index=self.index,
            # query={"match": {"name": genre_name}},
            query={"match_phrase": {"name": {"query": genre_name}}},
        )
        for doc in data.body["hits"]["hits"]:
            if doc:
                return Genre(**doc["_source"])
            return None

    async def get_genre_by_name(self, genre_name: str) -> Optional[BaseModel]:
        genre = await self._get_from_cache(key=genre_name)
        if not genre:
            genre = await self._get_genre_by_name_from_elastic(genre_name)
            if not genre:
                return None

            await self._put_to_cache(key=genre_name, data=genre)

        return genre


@lru_cache()
def get_genre_service(
    state: State = Depends(get_storage),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> BaseService:
    return GenreService(state, elastic)
