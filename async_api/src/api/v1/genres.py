import inspect
from http import HTTPStatus
from typing import List

from core import config
from dto.dto import GenreDTO
from fastapi import APIRouter, Depends, HTTPException, Response
from models.genre import Genre
from services.film import FilmService, get_film_service

from utils.utils import get_pagination_params, template_cache_key

router = APIRouter()

@router.get("/{genre_id}", response_model=GenreDTO, description="Детальная информация по жанру.")
async def genre_details(genre_id: str, film_service: FilmService = Depends(get_film_service)) -> GenreDTO:
    genre = await film_service.get_genre_by_id(genre_id)
    if not genre:
        # Если жанр не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum, такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")

    return genre


@router.get("", response_model=List[GenreDTO], description="Список жанров")
async def get_genres(
    response: Response,
    film_service: FilmService = Depends(get_film_service),
    pagination: dict = Depends(get_pagination_params),
) -> List[Genre]:
    # Get the page and per_page values from the pagination dictionary
    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page

    func_name = inspect.currentframe().f_code.co_name
    template = template_cache_key(pagination=pagination, sort_queries=None, filter_query=None, filter_=None, func_name=func_name)

    genres = await film_service.get_objects(
        index="genres",
        per_page=per_page,
        offset=offset,
        sort=None,
        search_query=None,
        cache_key=template,
        model=Genre,
        expire=config.GENRE_CACHE_EXPIRE_IN_SECONDS,
    )
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genres not found")

    # Send some extra information in the response headers
    # so the client can retrieve it as needed
    response.headers["x-total-count"] = str(len(genres))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return genres
