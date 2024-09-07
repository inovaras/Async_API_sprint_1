from enum import Enum
from http import HTTPStatus
from typing import List

from dto.dto import FilmDetailsDTO, FilmDTO
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from models.film import Film
from models.genre import Genre
from pydantic import BaseModel
from services.film import FilmService, get_film_service
from core import config
import inspect

router = APIRouter()


# Define a dependency function that returns the pagination parameters
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


class FilterBy(str, Enum):
    """Поля разрешенные для фильтрации."""

    imdb_rating = "imdb_rating"
    title = "title"
    description = "description"
    genres = "genres"
    actors = "actors"
    directors = "directors"
    writers = "writers"


class FilterBySearch(str, Enum):
    """Поля разрешенные для фильтрации."""

    title = "title"
    description = "description"


class SortQueryParams(BaseModel):
    sort_by: str | None = None


class FilterQueryParams(BaseModel):
    need_filter: bool = False
    filter_by: FilterBy = FilterBy.imdb_rating
    query: str | None = None


class FilterQueryParamsSearch(BaseModel):
    filter_by: FilterBySearch = FilterBySearch.title
    query: str


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get("/{film_id}", response_model=FilmDetailsDTO, description="Детальная информация по фильму.")
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_film_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum    # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    if film.genres:
        genres: List[Genre] = []
        for genre_name in film.genres:
            genre: Genre | None = await film_service.get_genre_by_name(genre_name=genre_name)
            if genre:
                genres.append(genre)
    film.genres = genres
    # Перекладываем данные из models.FilmDTO в FilmDTO
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и формирования ответов API,
    # вы бы предоставляли клиентам данные, которые им не нужны
    # и, возможно, данные, которые опасно возвращать
    # return FilmDTO(id=film.id, title=film.title, imdb_rating=film.imdb_rating, actors=film.actors)
    # return FilmDTO(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
    return film


@router.get("/search/", response_model=List[FilmDTO], description="Нечеткий поиск фильмов по заголовку или описанию.")
async def search_by_films(
    response: Response,
    query: FilterQueryParamsSearch = Depends(),
    pagination: dict = Depends(get_pagination_params),
    film_service: FilmService = Depends(get_film_service),
) -> List[FilmDTO]:
    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page
    pagination_query = f"{page}_{per_page}"
    func_name = inspect.currentframe().f_code.co_name
    template = f"{func_name}_{pagination_query}"


    if query.filter_by in ["title", "description"]:
        filters = []
        words = query.query.split(" ")
        for word in words:
            filters.append(
                {"fuzzy": {query.filter_by: {"value": word, "fuzziness": "AUTO"}}},
            )
        filter_query = {"bool": {"should": filters}}

    films = await film_service.get_objects(
        index="movies",
        per_page=per_page,
        offset=offset,
        sort=None,
        search_query=filter_query,
        cache_key=f"{template}_{query.filter_by}_{query.query}",
        model=Film,
        expire=config.FILM_CACHE_EXPIRE_IN_SECONDS,
    )

    response.headers["x-total-count"] = str(len(films))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return films


@router.get("", response_model=List[FilmDTO], description="Поиск фильмов с возможностью сортировки по рейтингу")
async def get_films(
    response: Response,
    film_service: FilmService = Depends(get_film_service),
    pagination: dict = Depends(get_pagination_params),
    sort: SortQueryParams = Depends(),
    filter_: FilterQueryParams = Depends(),
) -> List[Film]:
    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page



    filter_query = None
    filters = []
    if filter_.need_filter:
        if filter_.query:
            # INFO фильтрация по рейтингу
            if filter_.filter_by == "imdb_rating":
                if not filter_.query.isdigit():
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST, detail="Filter by imdb_rating must be int or float"
                    )
                filter_.query = float(filter_.query)
                filter_query = {"term": {filter_.filter_by: filter_.query}}
            else:
                # INFO поиск в List[str]
                if filter_.filter_by == "genres":
                    genre_model: Genre | None = await film_service._get_from_elastic(
                        id_=filter_.query, index="genres", model=Genre
                    )
                    if genre_model and filter_.need_filter:
                        filter_query = {"match": {filter_.filter_by: genre_model.name}}

                # INFO поиск в списке по имени
                if filter_.filter_by in ["actors", "directors", "writers"]:
                    filter_query = {
                        "bool": {
                            "must": [
                                # {"match": {"title": "eggs"}},
                                {
                                    "nested": {
                                        "path": filter_.filter_by,
                                        "query": {
                                            "bool": {
                                                "must": [
                                                    # {"match": {f"{filter_.filter_by}.name": filter_.query}},
                                                    {
                                                        "match_phrase": {
                                                            f"{filter_.filter_by}.name": {"query": filter_.query}
                                                        }
                                                    }
                                                ]
                                            }
                                        },
                                    }
                                },
                            ]
                        }
                    }
                # INFO нечеткий поиск
                if filter_.filter_by in ["title", "description"]:
                    filters = []
                    words = filter_.query.split(" ")
                    for word in words:
                        filters.append(
                            {"fuzzy": {filter_.filter_by: {"value": word, "fuzziness": "AUTO"}}},
                        )
                    filter_query = {"bool": {"should": filters}}

    # сортировка по релевантности запросу, если не включена сортировка по рейтингу.
    sort_queries = [{"_score": "desc"}]
    if sort.sort_by is not None:
        if sort.sort_by not in ["-imdb_rating", "imdb_rating"]:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Разрешенная сортировка: "-imdb_rating", "imdb_rating"')
        if sort.sort_by == "-imdb_rating":
            sort.sort_by = "desc"
        elif sort.sort_by == "imdb_rating":
            sort.sort_by = "asc"
        sort_queries = [{"imdb_rating": sort.sort_by}]

    func_name = inspect.currentframe().f_code.co_name
    template = f"{func_name}_{page}_{offset}"
    if filter_query:
        cache_key = f"{template}_{filter_.filter_by}_{filter_.query}"
    else:
        cache_key = f"{template}_without_filter"

    films = await film_service.get_objects(
        index="movies",
        per_page=per_page,
        offset=offset,
        sort=sort_queries,
        search_query=filter_query,
        cache_key=cache_key,
        model=Film,
        expire=config.FILM_CACHE_EXPIRE_IN_SECONDS,
    )

    # Send some extra information in the response headers
    # so the client can retrieve it as needed
    response.headers["x-total-count"] = str(len(films))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return films
