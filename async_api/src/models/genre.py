import datetime

from pydantic import BaseModel, Field


class Genre(BaseModel):
    id: str = Field()
    name: str = Field()
    description: str | None = Field()
