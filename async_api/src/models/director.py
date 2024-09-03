import datetime
from typing import List

from pydantic import BaseModel, Field

from models.film import Film


class Director(BaseModel):
    id: str = Field()
    first_name: str = Field()
    last_name: str = Field()
    films: List[Film] | None = Field()