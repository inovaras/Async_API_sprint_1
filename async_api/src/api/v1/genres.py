from enum import Enum
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from dto.dto import PersonDetailsDTO
from services.film import FilmService, get_film_service

router = APIRouter()
