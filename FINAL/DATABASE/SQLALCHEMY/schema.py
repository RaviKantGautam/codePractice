from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    name: str
    email: EmailStr

class PostSchema(BaseModel):
    title: str
    content: str | None = None
    author_id: int

class UserSchemaOut(UserSchema):
    id: int

    class Config:
        # Enable ORM mode to work with SQLAlchemy models
        orm_mode = True

class PostSchemaOut(PostSchema):
    id: int

    class Config:
        # Enable ORM mode to work with SQLAlchemy models
        orm_mode = True