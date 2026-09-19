from pydantic import BaseModel, Field, field_validator
from typing import Annotated
from fastapi import Query, FastAPI, Path

app = FastAPI()

class User(BaseModel):
    id: int = Field(default=None, description="ID of the user")
    name: str = Field(max_length=100, description="Name of the user")
    email: str = Field(max_length=100, description="Email of the user")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if "@" not in value:
            raise ValueError("Invalid email address")
        return value

class FilterQuery(BaseModel):
    limit: int = Field(default=10, max_length=100, min_length=1)
    offset: int = Field(default=0, max_length=100, min_length=0)
    search: str = Field(default="", description="Search query string", max_length=100)

@app.get("/filter")
def filter_query(filter: Annotated[FilterQuery, Query()]):
    return filter

@app.get("/filter/{item_id}")
def filter_query_item(item_id: int = Path(..., description="ID of the item", le=100, gt=0)):
    return {"item_id": item_id}

