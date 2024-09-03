# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from typing import List

from models.role import Role
from pydantic import BaseModel, Field


class Film(BaseModel):
    id: str = Field()
    title: str = Field()
    description: str | None = Field()
    imdb_rating: float | None = Field()
    genres: List[str] | None = Field()
    directors: List[Role] | None = Field()
    actors: List[Role] | None = Field()
    writers: List[Role] | None = Field()
    directors_names: List[str] | None = Field()
    actors_names: List[str] | None = Field()
    writers_names: List[str] | None = Field()

    # created_date
    # film_link