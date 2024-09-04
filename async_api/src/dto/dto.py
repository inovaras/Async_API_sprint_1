from typing import List

from models.role import Role
from pydantic import BaseModel


class FilmDTO(BaseModel):
    id: str
    title: str
    imdb_rating: float | None
    genres: List[str] | None
    directors: List[Role] | None
    actors: List[Role] | None
    writers: List[Role] | None


class FilmDetailsDTO(BaseModel):
    id: str
    title: str
    description: str | None
    imdb_rating: float | None
    genres: List[str] | None
    directors: List[Role] | None
    actors: List[Role] | None
    writers: List[Role] | None
    directors_names: List[str] | None
    actors_names: List[str] | None
    writers_names: List[str] | None
    # отсутствует в индексе
    created_date: str | None
    film_link: str | None
