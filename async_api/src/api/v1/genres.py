from http import HTTPStatus
from typing import List

from dto.dto import GenreDTO
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from models.genre import Genre
from services.genre import GenreService, get_genre_service
from utils.utils import get_pagination_params, update_headers

router = APIRouter()


@router.get("/{genre_id}", response_model=GenreDTO, description="Детальная информация по жанру.")
async def genre_details(genre_id: str, genre_service: GenreService = Depends(get_genre_service)) -> GenreDTO:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")

    return genre


@router.get("", response_model=List[GenreDTO], description="Список жанров")
async def get_genres(
    request: Request,
    response: Response,
    genre_service: GenreService = Depends(get_genre_service),
    pagination: dict = Depends(get_pagination_params),
) -> List[Genre]:
    genres = await genre_service.get_objects(request=request)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Genres not found")

    await update_headers(response, pagination, genres)

    return genres
