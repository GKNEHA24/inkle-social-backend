from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

users = []
posts = []

# User signup
class User(BaseModel):
    username: str
    password: str

@app.post("/signup")
def signup(user: User):
    users.append(user.dict())
    return {"msg": f"User {user.username} created"}

# User login
@app.post("/login")
def login(user: User):
    for u in users:
        if u['username'] == user.username and u['password'] == user.password:
            # In real projects, return a JWT here
            return {"msg": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Post create
class Post(BaseModel):
    username: str
    content: str

@app.post("/posts")
def create_post(post: Post):
    posts.append(post.dict())
    return {"msg": "Post created", "post": post}

# Get all posts
@app.get("/posts")
def get_posts():
    return {"posts": posts}
