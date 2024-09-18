from http import HTTPStatus
from typing import List

from dto.dto import FilmDetailsDTO, FilmDTO
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from models.film import Film
from models.genre import Genre
from services.film import BaseService, get_film_service
from services.genre import get_genre_service
from utils.utils import (
    FilmsFilterQueryParams,
    FilmsFilterQueryParamsSearch,
    FilmsSortQueryParams,
    get_pagination_params,
    update_headers,
)

router = APIRouter()


@router.get(
    "/search",
    response_model=List[FilmDTO],
    description="Нечеткий поиск фильмов по заголовку или описанию.",
)
async def search_by_films(
    request: Request,
    response: Response,
    query: FilmsFilterQueryParamsSearch = Depends(),
    pagination: dict = Depends(get_pagination_params),
    film_service: BaseService = Depends(get_film_service),
) -> List[FilmDTO]:
    """query забираю из request.url. Не удалять!"""
    films = await film_service.get_objects(request=request)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Films not found")

    await update_headers(response, pagination, films)

    return films



# Внедряем FilmService с помощью Depends(get_film_service)
@router.get(
    "/{film_id}",
    response_model=FilmDetailsDTO,
    description="Детальная информация по фильму.",
)
async def film_details(
    film_id: str,
    film_service: BaseService = Depends(get_film_service),
    genre_service: BaseService = Depends(get_genre_service),
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum, такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Film not found")

    if film.genres:
        genres: List[Genre] = []
        for genre_name in film.genres:
            genre: Genre | None = await genre_service.get_genre_by_name(genre_name=genre_name)
            if genre:
                genres.append(genre)
    film.genres = genres

    return film




@router.get(
    "",
    response_model=List[FilmDTO],
    description="Поиск фильмов с возможностью сортировки по рейтингу",
)
async def get_films(
    request: Request,
    response: Response,
    film_service: BaseService = Depends(get_film_service),
    genre_service: BaseService = Depends(get_genre_service),
    pagination: dict = Depends(get_pagination_params),
    sort: FilmsSortQueryParams = Depends(),
    filter_: FilmsFilterQueryParams = Depends(),
) -> List[Film]:
    if sort.sort_by is not None:
        if sort.sort_by not in ["-imdb_rating", "imdb_rating"]:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Разрешенная сортировка: "-imdb_rating", "imdb_rating"',
            )

    if filter_.query:
        if filter_.filter_by == "imdb_rating":
            if not filter_.query.isdigit():
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Filter by imdb_rating must be int or float",
                )
        else:
            if filter_.filter_by == "genre":
                # Поиск в genres регистрозависимый, тк mapping для genres - "text", а не "keyword".
                # Чтобы поиск удался, первую букву делаю заглавной.
                filter_.query = filter_.query.capitalize()
                genre_model: Genre | None = await genre_service.get_genre_by_name(genre_name=filter_.query)
                if not genre_model:
                    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Genre not found")
                request.query_params.__dict__["_dict"]["genre"] = genre_model.name

    films = await film_service.get_objects(request=request)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Films not found")

    await update_headers(response, pagination, films)

    return films
