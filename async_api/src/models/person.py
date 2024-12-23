import datetime
from typing import List

from pydantic import BaseModel, Field


class Person(BaseModel):
    id: str = Field()
    full_name: str = Field()
    movies: List[str] = Field(default=None)
