from enum import Enum
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from dto.dto import FilmDTO, FilmDetailsDTO
from models.film import Film
from pydantic import BaseModel
from services.film import FilmService, get_film_service

router = APIRouter()




# Внедряем FilmService с помощью Depends(get_film_service)
@router.get("/{film_id}", response_model=FilmDetailsDTO, description="Вся информация по фильму.")
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum    # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    # Перекладываем данные из models.FilmDTO в FilmDTO
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и формирования ответов API,
    # вы бы предоставляли клиентам данные, которые им не нужны
    # и, возможно, данные, которые опасно возвращать
    # return FilmDTO(id=film.id, title=film.title, imdb_rating=film.imdb_rating, actors=film.actors)
    # return FilmDTO(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
    return film


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


@router.get("/search/", response_model=List[FilmDTO], description="Нечеткий поиск фильмов по заголовку или описанию.")
async def search_by_films(
    response: Response,
    query: FilterQueryParamsSearch = Depends(),
    pagination: dict = Depends(get_pagination_params),
    film_service: FilmService = Depends(get_film_service),
) -> List[FilmDTO]:

    if query.filter_by in ["title", "description"]:
        filters = []
        words = query.query.split(" ")
        for word in words:
            filters.append(
                {"fuzzy": {query.filter_by: {"value": word, "fuzziness": "AUTO"}}},
            )
        filter_query = {"bool": {"should": filters}}

    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page

    films = await film_service.get_films(
        index="movies",
        per_page=per_page,
        offset=offset,
        sort=None,
        films_filter=filter_query,
    )

    response.headers["x-total-count"] = str(len(films))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return films


# @lru_cache()
@router.get("", response_model=List[FilmDTO], description="Поиск фильмов с возможностью сортировки по рейтингу")
async def get_films(
    response: Response,
    film_service: FilmService = Depends(get_film_service),
    pagination: dict = Depends(get_pagination_params),
    sort: SortQueryParams = Depends(),
    filter_: FilterQueryParams = Depends(),
) -> List[Film]:
    # Get the page and per_page values from the pagination dictionary
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
                    filter_query = {"match": {filter_.filter_by: filter_.query}}
                    # filter_query = {"match": {"genres": "history"}}

                # INFO поиск в списке по имени (Lucas == Luca). Search in List[{"id":1,"name":val}]
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
                                                    {"match": {f"{filter_.filter_by}.name": filter_.query}},
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

    # if genre:
    #     # genre_model: Genre = await film_service._get_genre_from_elastic("b92ef010-5e4c-4fd0-99d6-41b6456272cd")
    #     # if genre_model and filter_.need_filter:
    #         #TODO filters = list or dict anytime
    #         # filters.append({"term": {"genres": genre_model.name}})
    #     filters.append({"term": {"genres": "fantasy"}})

    sort_queries = [{"_score": "desc"}]
    if sort.sort_by is not None:
        if sort.sort_by == "-imdb_rating":
            sort.sort_by = "desc"
        elif sort.sort_by == "imdb_rating":
            sort.sort_by = "asc"
        sort_queries.append({"imdb_rating": sort.sort_by})

    films = await film_service.get_films(
        index="movies",
        per_page=per_page,
        offset=offset,
        sort=sort_queries,
        films_filter=filter_query,
    )

    # Send some extra information in the response headers
    # so the client can retrieve it as needed
    response.headers["x-total-count"] = str(len(films))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return films
