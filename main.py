from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# In-memory "databases"
users = []
posts = []
activities = []
follows = []
blocks = []
roles = {}

# Models
class User(BaseModel):
    username: str
    password: str

class Post(BaseModel):
    post_id: int
    username: str
    content: str

class LikeModel(BaseModel):
    username: str
    post_id: int

class FollowModel(BaseModel):
    follower: str
    following: str

class BlockModel(BaseModel):
    blocker: str
    blocked: str

class AdminActionModel(BaseModel):
    requester: str
    target_username: str

class OwnerActionModel(BaseModel):
    requester: str
    target_username: str

# Helper functions
def get_role(username):
    return roles.get(username, "user")

def require_role(username, allowed):
    if get_role(username) not in allowed:
        raise HTTPException(status_code=403, detail="Permission denied")

def user_exists(username):
    return any(u['username'] == username for u in users)

# User signup
@app.post("/signup")
def signup(user: User):
    if user_exists(user.username):
        raise HTTPException(status_code=409, detail="User exists")
    users.append(user.dict())
    roles[user.username] = "user" if users else "owner"
    activities.append({"message": f"{user.username} signed up"})
    return {"msg": f"User {user.username} created"}

# User login
@app.post("/login")
def login(user: User):
    for u in users:
        if u['username'] == user.username and u['password'] == user.password:
            return {"msg": "Login successful", "role": get_role(user.username)}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Create Post
@app.post("/posts")
def create_post(post: Post):
    if not user_exists(post.username):
        raise HTTPException(status_code=404, detail="User not found")
    posts.append(post.dict())
    activities.append({"message": f"{post.username} made a post"})
    return {"msg": "Post created", "post": post}

@app.get("/posts")
def get_posts(username: str):
    # Exclude blocked users' posts
    blocked_by = [b['blocked'] for b in blocks if b['blocker'] == username]
    return {"posts": [p for p in posts if p["username"] not in blocked_by]}

# Like a post
@app.post("/like")
def like_post(like: LikeModel):
    if not user_exists(like.username):
        raise HTTPException(status_code=404, detail="User not found")
    for p in posts:
        if p["post_id"] == like.post_id:
            activities.append({"message": f"{like.username} liked {p['username']}'s post"})
            return {"msg": f"User {like.username} liked post {like.post_id}"}
    raise HTTPException(status_code=404, detail="Post not found")

# Follow a user
@app.post("/follow")
def follow_user(follow: FollowModel):
    if not user_exists(follow.follower) or not user_exists(follow.following):
        raise HTTPException(status_code=404, detail="User not found")
    follows.append(follow.dict())
    activities.append({"message": f"{follow.follower} followed {follow.following}"})
    return {"msg": f"{follow.follower} followed {follow.following}"}

# Block a user
@app.post("/block")
def block_user(block: BlockModel):
    if not user_exists(block.blocker) or not user_exists(block.blocked):
        raise HTTPException(status_code=404, detail="User not found")
    blocks.append(block.dict())
    activities.append({"message": f"{block.blocker} blocked {block.blocked}"})
    return {"msg": f"{block.blocker} blocked {block.blocked}"}

# Activity feed
@app.get("/activity")
def get_activity():
    return {"activities": activities[-50:]}

# Admin delete user
@app.delete("/admin/delete_user")
def admin_delete_user(data: AdminActionModel):
    require_role(data.requester, ["admin", "owner"])
    global users
    users = [u for u in users if u['username'] != data.target_username]
    activities.append({"message": f"User {data.target_username} deleted by '{data.requester}'"})
    return {"msg": f"User {data.target_username} deleted"}

# Admin delete post
@app.delete("/admin/delete_post")
def admin_delete_post(requester: str, post_id: int):
    require_role(requester, ["admin", "owner"])
    global posts
    posts = [p for p in posts if p['post_id'] != post_id]
    activities.append({"message": f"Post {post_id} deleted by '{requester}'"})
    return {"msg": f"Post {post_id} deleted"}

# Owner: add/remove admin
@app.post("/owner/add_admin")
def add_admin(data: OwnerActionModel):
    require_role(data.requester, ["owner"])
    if not user_exists(data.target_username):
        raise HTTPException(status_code=404, detail="Target user not found")
    roles[data.target_username] = "admin"
    activities.append({"message": f"{data.target_username} promoted to admin by '{data.requester}'"})
    return {"msg": f"{data.target_username} added as admin"}

@app.post("/owner/remove_admin")
def remove_admin(data: OwnerActionModel):
    require_role(data.requester, ["owner"])
    if not user_exists(data.target_username):
        raise HTTPException(status_code=404, detail="Target user not found")
    roles[data.target_username] = "user"
    activities.append({"message": f"{data.target_username} demoted to user by '{data.requester}'"})
    return {"msg": f"{data.target_username} removed as admin"}
