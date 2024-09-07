from enum import Enum
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from models.genre import Genre
from pydantic import BaseModel
from dto.dto import GenreDTO
from services.genre import GenreService, get_genre_service

router = APIRouter()


# Define a dependency function that returns the pagination parameters
def get_pagination_params(
    # page must be greater than 0
    page: int = Query(1, gt=0),
    # per_page must be greater than 0
    per_page: int = Query(10, gt=0),
):
    return {"page": page, "per_page": per_page}



@router.get("/{genre_id}", response_model=GenreDTO, description="Детальная информация по жанру.")
async def genre_details(genre_id: str, genre_service: GenreService = Depends(get_genre_service)) -> GenreDTO:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        # Если жанр не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum    # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")

    return genre


@router.get("", response_model=List[GenreDTO], description="Список жанров")
async def get_genres(
    response: Response,
    genre_service: GenreService = Depends(get_genre_service),
    pagination: dict = Depends(get_pagination_params),
) -> List[Genre]:
    # Get the page and per_page values from the pagination dictionary
    page = pagination["page"]
    per_page = pagination["per_page"]
    offset = (page - 1) * per_page

    genres = await genre_service.get_genres(
        index="genres",
        per_page=per_page,
        offset=offset,
    )

    # Send some extra information in the response headers
    # so the client can retrieve it as needed
    response.headers["x-total-count"] = str(len(genres))
    response.headers["x-page"] = str(page)
    response.headers["x-per-page"] = str(per_page)

    return genres