from enum import Enum
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from dto.dto import PersonDTO, PersonDetailsDTO
from services.film import FilmService, get_film_service

router = APIRouter()


class FilmDTO(BaseModel):
    id: str
    title: str
    imdb_rating: float | None


# @router.get("/search/", response_model=FilmDTO)


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get("/{person_id}", response_model=PersonDetailsDTO)
async def person_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> PersonDetailsDTO:
    person = await film_service.get_person_by_id(film_id)
    if not person:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum    # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    # TODO get films by id
    dto = PersonDetailsDTO(uuid=person.id, full_name=person.full_name, films=[])

    # for film_id in person.movies:
    #     film = await film_service.get_by_id(film_id=film_id)
    #     dto.films.append({"uuid": film.id, "roles": []})
    #     for role in film.actors, :
    #         if role.id == person.id:
    #             dto.films[0].update({"roles": "actors"})
    #     for role in film.directors:
    #         if role.id == person.id:

    #     for role in film.writers:
    #         if role.id == person.id:

    #     print()

    return person


@router.get("/{person_id}/film/", response_model=FilmDTO)

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


class FilterBySearch(str, Enum):
    """Поля разрешенные для фильтрации."""

    full_name = "full_name"


class FilterQueryParamsSearch(BaseModel):
    filter_by: FilterBySearch = FilterBySearch.full_name
    query: str


@router.get("/search/", response_model=List[PersonDTO], description="Нечеткий поиск персоналий по ФИО.")
async def search_by_persons(
    response: Response,
    query: FilterQueryParamsSearch = Depends(),
    pagination: dict = Depends(get_pagination_params),
    film_service: FilmService = Depends(get_film_service),
) -> List[PersonDTO]:

    if query.filter_by in ["full_name"]:
        # filter_query = { "match_phrase": { "message": {"query":"George Lucas", "analyzer": "ru_en"} }}
        filter_query = {"match": {"full_name": query.query}}
        # filter_query = {"bool": {"should": [{"term": {"full_name": "George"}}, {"term": {"full_name": "Lucas"}}]}}


    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page

    persons = await film_service.get_persons(
        index="persons",
        per_page=per_page,
        offset=offset,
        sort=None,
        persons_filter=filter_query,
    )

    response.headers["x-total-count"] = str(len(persons))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return persons
