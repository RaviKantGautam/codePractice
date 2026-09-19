# SQL ORM QUERIES

# Example SQLAlchemy ORM queries using the session object
from FINAL.DATABASE.SQLALCHEMY.sync_model import User, Post, session
from sqlalchemy import func

# Create a new user
new_user = User(name="John Doe", email="john.doe@example.com")
db = session()
db.add(new_user)
db.commit()
db.refresh(new_user)
print(new_user)
db.close()

# Query all users
db = session()
all_users = db.query(User).all()
print(all_users)
db.close()

# Create a new post
new_post = Post(title="My First Post", content="This is the content of my first post.", author_id=new_user.id)
db = session()
db.add(new_post)
db.commit()
db.refresh(new_post)
print(new_post)
db.close()

# Query all posts
db = session()
all_posts = db.query(Post).all()
print(all_posts)
db.close()

# Join users and posts
db = session()
user_posts = db.query(User, Post).join(Post, User.id == Post.author_id).all()
for user, post in user_posts:
    print(f"User: {user.name}, Post: {post.title}")
db.close()

# write a query to get all posts by a specific user with post title in capital letters
specific_user_id = new_user.id
db = session()
user_posts = db.query(Post).filter(Post.author_id == specific_user_id).all()
for post in user_posts:
    print(f"Post: {post.title.upper()}")
db.close()


# write a query to get all users who have written at least one post
db = session()
users_with_posts = db.query(User).join(Post, User.id == Post.author_id).distinct().all()
for user in users_with_posts:
    print(f"User: {user.name}")
db.close()

# write a query to get count of posts by each user
db = session()
post_counts = db.query(User, func.count(Post.id)).join(Post, User.id == Post.author_id).group_by(User.id).all()
for user, count in post_counts:
    print(f"User: {user.name}, Post Count: {count}")
db.close()

# write a query to get the most recent post by each user
db = session()
subquery = db.query(Post.author_id, func.max(Post.id).label("max_post_id")).group_by(Post.author_id).subquery()
recent_posts = db.query(Post).join(subquery, Post.id == subquery.c.max_post_id).all()
for post in recent_posts:
    print(f"User ID: {post.author_id}, Most Recent Post: {post.title}")
db.close()

# write a query to get all users who have not written any posts
db = session()
users_without_posts = db.query(User).outerjoin(Post, User.id == Post.author_id).filter(Post.id == None).all()
for user in users_without_posts:
    print(f"User: {user.name}")
db.close()

