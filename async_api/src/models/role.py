from typing import Any, List

from pydantic import BaseModel, Field


class Role(BaseModel):
    id: str|None = Field()
    name: str|None = Field()
    films: List[str] | None = Field(default=None)
