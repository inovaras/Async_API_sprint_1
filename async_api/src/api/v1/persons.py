from enum import Enum
from http import HTTPStatus
from typing import List

from models.film import Film
from core import config
from dto.dto import FilmDTO, PersonDetailsDTO
from fastapi import APIRouter, Depends, HTTPException, Response
from models.person import Person
from pydantic import BaseModel
from services.film import FilmService, get_film_service
import inspect
from utils.utils import get_pagination_params, PersonsFilterQueryParamsSearch, template_cache_key

router = APIRouter()


async def person_to_dto(person: Person, film_service: FilmService) -> PersonDetailsDTO:
    dto = PersonDetailsDTO(id=person.id, full_name=person.full_name, films=[])
    for i, film_id in enumerate(person.movies):
        film = await film_service.get_film_by_id(film_id=film_id)
        dto.films.append({"uuid": film.id, "roles": []})  # type: ignore
        if dto.full_name in film.actors_names:  # type: ignore
            dto.films[i]["roles"].append("actor")  # type: ignore
        if dto.full_name in film.directors_names:  # type: ignore
            dto.films[i]["roles"].append("director")  # type: ignore
        if dto.full_name in film.writers_names:  # type: ignore
            dto.films[i]["roles"].append("writer")  # type: ignore

    return dto


@router.get("/{person_id}", response_model=PersonDetailsDTO, description="Детальная информация по персоне.")
async def person_details(person_id: str, film_service: FilmService = Depends(get_film_service)) -> PersonDetailsDTO:
    person = await film_service.get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Person not found")

    return await person_to_dto(person=person, film_service=film_service)


@router.get("/search/", response_model=List[PersonDetailsDTO], description="Точный фразовый поиск персон по ФИО.")
async def search_by_persons(
    response: Response,
    query: PersonsFilterQueryParamsSearch = Depends(),
    pagination: dict = Depends(get_pagination_params),
    film_service: FilmService = Depends(get_film_service),
) -> List[PersonDetailsDTO]:
    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page

    func_name = inspect.currentframe().f_code.co_name

    filter_query = {"match_phrase": {"full_name": {"query": query.query}}}
    template = template_cache_key(pagination=pagination, sort_queries=None, filter_query=filter_query, filter_=query, func_name=func_name)

    persons = await film_service.get_objects(
        index="persons",
        per_page=per_page,
        offset=offset,
        sort=None,
        search_query=filter_query,
        cache_key=template,
        model=Person,
        expire=config.PERSON_CACHE_EXPIRE_IN_SECONDS,
    )

    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Persons not found")

    result: List[PersonDetailsDTO] = []
    for person in persons:
        dto = await person_to_dto(person=person, film_service=film_service)
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

    func_name = inspect.currentframe().f_code.co_name
    template = template_cache_key(pagination=pagination, sort_queries=None, filter_query=None, filter_=None, func_name=func_name )

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

    films = await film_service.get_objects(
        index="movies",
        per_page=per_page,
        offset=offset,
        sort=None,
        search_query=films_filter,
        cache_key=template,
        model=Film,
        expire=config.FILM_CACHE_EXPIRE_IN_SECONDS,
    )

    response.headers["x-total-count"] = str(len(films))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return films
