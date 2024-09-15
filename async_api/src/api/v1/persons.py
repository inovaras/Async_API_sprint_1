from http import HTTPStatus
from typing import List

from dto.dto import FilmDTO, PersonDetailsDTO
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from models.person import Person
from services.film import BaseService, FilmService, get_film_service
from services.person import get_person_service
from utils.utils import (
    PersonsFilterQueryParamsSearch,
    get_pagination_params,
    update_headers,
)

router = APIRouter()


async def person_to_dto(person: Person, film_service: FilmService) -> PersonDetailsDTO:
    dto = PersonDetailsDTO(id=person.id, full_name=person.full_name, films=[])
    for i, film_id in enumerate(person.movies):
        film = await film_service.get_by_id(id_=film_id)
        dto.films.append({"uuid": film.id, "roles": []})  # type: ignore
        if film:
            if dto.full_name in film.actors_names:  # type: ignore
                dto.films[i]["roles"].append("actor")  # type: ignore
            if dto.full_name in film.directors_names:  # type: ignore
                dto.films[i]["roles"].append("director")  # type: ignore
            if dto.full_name in film.writers_names:  # type: ignore
                dto.films[i]["roles"].append("writer")  # type: ignore

    return dto



@router.get(
    "/search",
    response_model=List[PersonDetailsDTO],
    description="Точный фразовый поиск персон по ФИО.",
)
async def search_by_persons(
    request: Request,
    response: Response,
    query: PersonsFilterQueryParamsSearch = Depends(),
    pagination: dict = Depends(get_pagination_params),
    person_service: BaseService = Depends(get_person_service),
    film_service: BaseService = Depends(get_film_service),
) -> List[PersonDetailsDTO]:
    """query для поискового запроса в еластик беру из request.url. Не удалять!"""
    persons = await person_service.get_objects(request=request)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Persons not found")

    result: List[PersonDetailsDTO] = []
    for person in persons:
        dto = await person_to_dto(person=person, film_service=film_service)
        result.append(dto)

    await update_headers(response, pagination, result)

    return result


@router.get(
    "/{person_id}",
    response_model=PersonDetailsDTO,
    description="Детальная информация по персоне.",
)
async def person_details(
    person_id: str,
    person_service: BaseService = Depends(get_person_service),
    film_service: BaseService = Depends(get_film_service),
) -> PersonDetailsDTO:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Person not found")

    return await person_to_dto(person=person, film_service=film_service)





@router.get(
    "/{person_id}/film",
    response_model=List[FilmDTO],
    description="Фильмы, в которых участвовала персона.",
)
async def person_films(
    request: Request,
    response: Response,
    person_id: str,
    person_service: BaseService = Depends(get_person_service),
    film_service: BaseService = Depends(get_film_service),
    pagination: dict = Depends(get_pagination_params),
) -> List[FilmDTO]:
    """person_id для поискового запроса в еластик беру из request.path_params"""
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Person not found")

    films = await film_service.get_objects(request=request)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Films not found")

    await update_headers(response, pagination, films)

    return films
