from enum import Enum
from typing import Iterable

from fastapi import Query, Response
from pydantic import BaseModel


async def update_headers(response: Response, pagination: dict, objects: Iterable) -> None:
    if objects:
        objects = str(len(objects))
    else:
        objects = "0"

    response.headers["x-total-count"] = objects
    response.headers["x-page"] = str(pagination["page"])
    response.headers["x-per-page"] = str(pagination["per_page"])


def get_pagination_params(
    # page must be greater than 0
    page: int = Query(1, gt=0),
    # per_page must be greater than 0
    per_page: int = Query(50, gt=0),
) -> dict:
    return {"page": page, "per_page": per_page}


class OrderBy(str, Enum):
    """Поля разрешенные для сортировки."""

    imdb_rating = "imdb_rating"


class PersonsFilterBy(str, Enum):
    """Поля разрешенные для фильтрации."""

    imdb_rating = "imdb_rating"
    title = "title"
    description = "description"


class PersonsFilterBySearch(str, Enum):
    """Поля разрешенные для фильтрации."""

    full_name = "full_name"


class PersonsSortQueryParams(BaseModel):
    need_sort: bool = False
    order_by: OrderBy = OrderBy.imdb_rating
    descending: bool = True


class PersonsFilterQueryParams(BaseModel):
    need_filter: bool = False
    filter_by: PersonsFilterBy = PersonsFilterBy.imdb_rating
    query: str | None = None


class PersonsFilterQueryParamsSearch(BaseModel):
    query: str


class FilmsFilterBy(str, Enum):
    """Поля разрешенные для фильтрации."""

    imdb_rating = "imdb_rating"
    title = "title"
    description = "description"
    genre = "genre"
    actors = "actors"
    directors = "directors"
    writers = "writers"


class FilmsFilterBySearch(str, Enum):
    """Поля разрешенные для фильтрации."""

    title = "title"
    description = "description"


class FilmsSortQueryParams(BaseModel):
    sort_by: str | None = None


class FilmsFilterQueryParams(BaseModel):
    filter_by: FilmsFilterBy| None = None
    query: str | None = None


class FilmsFilterQueryParamsSearch(BaseModel):
    query: str
