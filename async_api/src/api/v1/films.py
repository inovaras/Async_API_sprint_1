from enum import Enum
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from services.film import FilmService, get_film_service

router = APIRouter()


class FilmDTO(BaseModel):
    id: str
    title: str
    imdb_rating: float | None


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get("/{film_id}", response_model=FilmDTO)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> FilmDTO:
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


class SortQueryParams(BaseModel):
    need_sort: bool = False
    order_by: OrderBy = OrderBy.imdb_rating
    descending: bool = True


class FilterQueryParams(BaseModel):
    need_filter: bool = False
    filter_by: FilterBy = FilterBy.imdb_rating
    query: str | None = None


@router.get("", response_model=List[FilmDTO])
async def get_films(
    response: Response,
    film_service: FilmService = Depends(get_film_service),
    pagination: dict = Depends(get_pagination_params),
    sort: SortQueryParams = Depends(),
    filter_: FilterQueryParams = Depends(),
) -> List[FilmDTO]:
    # Get the page and per_page values from the pagination dictionary
    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page

    filters = []
    if filter_.need_filter:
        if filter_.query:
            if filter_.filter_by == "imdb_rating":  # FIXME hardcode
                filter_.query = float(filter_.query)
                filters = {"term": {filter_.filter_by: filter_.query}}
            else:
                words = filter_.query.split(" ")
                for word in words:
                    filters.append(
                        {"fuzzy": {filter_.filter_by: {"value": word, "fuzziness": "AUTO"}}},
                    )

    sort_queries = [{"_score": "desc"}]
    if sort.need_sort:
        if sort.descending == True:
            sort.descending = "desc"
        else:
            sort.descending = "asc"
        sort_queries.append({sort.order_by: sort.descending})

    films = await film_service.get_films(
        index="movies",
        per_page=per_page,
        offset=offset,
        sort=sort_queries,
        films_filter=filters,
    )

    # Send some extra information in the response headers
    # so the client can retrieve it as needed
    response.headers["x-total-count"] = str(len(films))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return films
