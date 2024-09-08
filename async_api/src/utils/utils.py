from enum import Enum
from pydantic import BaseModel
from fastapi import Query


def get_pagination_params(
    # page must be greater than 0
    page: int = Query(1, gt=0),
    # per_page must be greater than 0
    per_page: int = Query(10, gt=0),
):
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
    filter_by: PersonsFilterBySearch = PersonsFilterBySearch.full_name
    query: str

class FilmsFilterBy(str, Enum):
    """Поля разрешенные для фильтрации."""

    imdb_rating = "imdb_rating"
    title = "title"
    description = "description"
    genres = "genres"
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
    need_filter: bool = False
    filter_by: FilmsFilterBy = FilmsFilterBy.imdb_rating
    query: str | None = None


class FilmsFilterQueryParamsSearch(BaseModel):
    filter_by: FilmsFilterBySearch = FilmsFilterBySearch.title
    query: str


def template_cache_key(pagination, sort_queries, filter_query, filter_, func_name: str) -> str:
    page = pagination["page"]
    per_page = pagination["per_page"]
    pagination_query = f"{page}_{per_page}"

    if sort_queries:
        pagination_query = f"{pagination['page']}_{pagination['per_page']}"
        template = f"{func_name}_{pagination_query}_{sort_queries}"
    else:
        template = f"{func_name}_{pagination_query}"

    if filter_query:
        template = f"{template}_{filter_.filter_by}_{filter_.query}"
    else:
        template = f"{template}_without_filter"

    return template
