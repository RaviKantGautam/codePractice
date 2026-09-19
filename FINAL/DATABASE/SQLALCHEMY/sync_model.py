from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, validates

engine = create_engine('sqlite:///example.db')
# Create the database engine and session for SQLAlchemy
Base = declarative_base()

# Define your models here
Base.metadata.create_all(engine)

# Create a new session instance for interacting with the database
session = sessionmaker( 
    autocommit=False,
    autoflush=True,
    bind=engine
)()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    posts = relationship('Post', back_populates='author')

    @validates('email')
    def validate_email(self, key, email):
        if '@' not in email:
            raise ValueError("Invalid email address")
        return email.lower()

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')