# SQLModel FastAPI example
from sqlmodel import SQLModel, Field, create_engine, Session, select
from fastapi import FastAPI, Depends

app = FastAPI()

# install SQLModel and FastAPI
# pip install sqlmodel fastapi uvicorn
# or
# uv add sqlmodel

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

class Item(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=255)

@app.post("/items/")
def create_item(item: Item, session: Session = Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.get("/items/{item_id}")
def read_item(item_id: int, session: Session = Depends(get_session)):
    statement = select(Item).where(Item.id == item_id)
    result = session.exec(statement)
    item = result.first()
    return item