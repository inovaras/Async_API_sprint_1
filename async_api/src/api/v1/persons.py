from enum import Enum
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from dto.dto import PersonDTO, PersonDetailsDTO, FilmDTO
from services.film import FilmService, get_film_service

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


class SortQueryParams(BaseModel):
    need_sort: bool = False
    order_by: OrderBy = OrderBy.imdb_rating
    descending: bool = True


class FilterQueryParams(BaseModel):
    need_filter: bool = False
    filter_by: FilterBy = FilterBy.imdb_rating
    query: str | None = None


class FilterBySearch(str, Enum):
    """Поля разрешенные для фильтрации."""

    full_name = "full_name"


class FilterQueryParamsSearch(BaseModel):
    filter_by: FilterBySearch = FilterBySearch.full_name
    query: str

# INFO CAHCED
@router.get("/{person_id}", response_model=PersonDetailsDTO, description="Детальная информация по персоне.")
async def person_details(person_id: str, film_service: FilmService = Depends(get_film_service)) -> PersonDetailsDTO:
    person = await film_service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    dto = PersonDetailsDTO(id=person.id, full_name=person.full_name, films=[])
    for i, film_id in enumerate(person.movies):
        film = await film_service.get_by_id(film_id=film_id)
        dto.films.append({"uuid": film.id, "roles": []})  # type: ignore
        if dto.full_name in film.actors_names:  # type: ignore
            dto.films[i]["roles"].append("actor")  # type: ignore
        if dto.full_name in film.directors_names:  # type: ignore
            dto.films[i]["roles"].append("director")  # type: ignore
        if dto.full_name in film.writers_names:  # type: ignore
            dto.films[i]["roles"].append("writer")  # type: ignore

    return dto


@router.get("/search/", response_model=List[PersonDetailsDTO], description="Точный фразовый поиск персон по ФИО.")
async def search_by_persons(
    response: Response,
    query: FilterQueryParamsSearch = Depends(),
    pagination: dict = Depends(get_pagination_params),
    film_service: FilmService = Depends(get_film_service),
) -> List[PersonDetailsDTO]:

    if query.filter_by in ["full_name"]:
        # filter_query = {"match": {"full_name": query.query}}
        filter_query = {"match_phrase": {"full_name": {"query": query.query}}}

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

    result: List[PersonDetailsDTO] = []
    for person in persons:
        dto = PersonDetailsDTO(id=person.id, full_name=person.full_name, films=[])
        for i, film_id in enumerate(person.movies):
            film = await film_service.get_by_id(film_id=film_id)
            dto.films.append({"uuid": film.id, "roles": []})  # type: ignore
            if dto.full_name in film.actors_names:  # type: ignore
                dto.films[i]["roles"].append("actor")  # type: ignore
            if dto.full_name in film.directors_names:  # type: ignore
                dto.films[i]["roles"].append("director")  # type: ignore
            if dto.full_name in film.writers_names:  # type: ignore
                dto.films[i]["roles"].append("writer")  # type: ignore
        result.append(dto)

    response.headers["x-total-count"] = str(len(persons))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return result


@router.get("/{person_id}/film", response_model=List[FilmDTO], description="Фильмы, в которых участвовала персона.")
async def person_films(
    person_id: str,
    response: Response,
    film_service: FilmService = Depends(get_film_service),
    pagination: dict = Depends(get_pagination_params),
) -> List[FilmDTO]:
    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page

    person = await film_service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    films_filter = {
        "bool": {
            "should": [
                {"nested": {"path": "directors", "query": {"term": {"directors.id": person.id}}}},
                {"nested": {"path": "writers", "query": {"term": {"writers.id": person.id}}}},
                {"nested": {"path": "actors", "query": {"term": {"actors.id": person.id}}}},
            ]
        }
    }

    films = await film_service.get_films(
        index="movies", per_page=per_page, offset=offset, sort=None, films_filter=films_filter
    )

    response.headers["x-total-count"] = str(len(films))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return films
