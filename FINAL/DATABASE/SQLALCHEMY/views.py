from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from FINAL.DATABASE.SQLALCHEMY.sync_model import User, Post, session
from FINAL.DATABASE.SQLALCHEMY.schema import UserSchema, PostSchema, UserSchemaOut, PostSchemaOut

@asynccontextmanager
async def get_db_async():
    db = session()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="My FastAPI App",
    description="This is a FastAPI application with SQLAlchemy integration.",
    version="1.0.0",
    contact="support@example.com",
    lifespan=get_db_async
)


@app.post("/users/", response_model=UserSchemaOut)
def create_user(user: UserSchema, db: Session = Depends(get_db_async)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/posts/", response_model=PostSchemaOut)
def create_post(post: PostSchema, db: Session = Depends(get_db_async)):
    db_post = Post(title=post.title, content=post.content, author_id=post.author_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/users/{user_id}", response_model=UserSchemaOut)
def get_user(user_id: int, db: Session = Depends(get_db_async)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/posts/{post_id}", response_model=PostSchemaOut)
def get_post(post_id: int, db: Session = Depends(get_db_async)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@app.get("/users/", response_model=list[UserSchemaOut])
def get_users(db: Session = Depends(get_db_async)):
    db_users = db.query(User).all()
    return db_users

@app.get("/posts/", response_model=list[PostSchemaOut])
def get_posts(db: Session = Depends(get_db_async)):
    db_posts = db.query(Post).all()
    return db_posts
