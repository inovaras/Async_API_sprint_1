from pydantic import BaseModel, Field


class Role(BaseModel):
    id: str = Field()
    name: str = Field()