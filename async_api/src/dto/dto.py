from typing import Dict, List

from models.genre import Genre
from models.role import Role
from pydantic import BaseModel


class FilmDTO(BaseModel):
    id: str
    title: str
    imdb_rating: float | None
    # genres: List[str] | None
    # directors: List[Role] | None
    # actors: List[Role] | None
    # writers: List[Role] | None


class FilmDetailsDTO(BaseModel):
    id: str
    title: str
    description: str | None
    imdb_rating: float | None
    genres: List[Genre] | None
    directors: List[Role] | None
    actors: List[Role] | None
    writers: List[Role] | None
    # отсутствует в индексе
    # TODO возможно надо убрать тк нет в примере "Полная информация по фильму" таких полей
    created_date: str | None
    film_link: str | None


class PersonDTO(BaseModel):
    id: str
    full_name: str
    # films: List[Dict[str, List[Role]]]

class PersonDetailsDTO(BaseModel):
    id: str
    full_name: str
    films: List[Dict[str, List[Role]]] | None