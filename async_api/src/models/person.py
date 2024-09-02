import datetime

from pydantic import BaseModel, Field


class Person(BaseModel):
    id: str = Field()
    full_name: str = Field()
