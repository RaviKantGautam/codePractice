from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import asyncio

engine = create_async_engine('sqlite+aiosqlite:///example.db', echo=True)

# Create the database engine and session for SQLAlchemy
Base = declarative_base()

# Define your models here
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(init_models())

# Create a new session instance for interacting with the database
async_session = sessionmaker(
    autocommit=False,
    autoflush=True,
    bind=engine,
    class_=AsyncSession
)()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    posts = relationship('Post', back_populates='author')

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')