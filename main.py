from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    username: str
    password: str

@app.post("/signup")
def signup(user: User):
    # Later: implement sign-up logic (saving the user to DB)
    return {"msg": f"User {user.username} created"}
