from fastapi import Cookie, FastAPI, Form, Request, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer

from .flowers_repository import Flower, FlowersRepository
from .purchases_repository import Purchase, PurchasesRepository
from .users_repository import User, UsersRepository

from pydantic import BaseModel, EmailStr

from typing import List
from jose import jwt
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

flowers_repository = FlowersRepository()
purchases_repository = PurchasesRepository()
users_repository = UsersRepository() 



def create_jwt(user_id: int) -> str:
    body = {"user_id": user_id}
    token = jwt.encode(body, "TorTokaeva", "HS256")
    return token

def decode_jwt(token: str) -> int:
    data = jwt.decode(token, "TorTokaeva", "HS256")
    return data["user_id"]

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserResponse(BaseModel):
    email: str
    full_name: str

@app.post("/signup")
def post_signup(user: CreateUserRequest):
    users_repository.signup(user.email, user.full_name, user.password)
    return {}

@app.post("/login")
def post_login(
    username: str = Form(),
    password: str = Form(),
):
    user = users_repository.get_user_by_email(username)
    if not user or user.password != password:
        return HTTPException(status_code=400, detail="Incorrect username or password")
    
    token = create_jwt(user.id)
    return {"access_token": token, "type": "bearer"}

@app.get("/profile", response_model = UserResponse)
def get_profile(token: str = Depends(oauth2_scheme)):
    user_id = decode_jwt(token)
    user = users_repository.get_user_by_id(user_id)
    return user

class FlowerRequestResponse(BaseModel):
    name: str
    count: int
    cost: int

@app.get("/flowers", response_model=List[FlowerRequestResponse])
def get_flowers(request: Request):
    return flowers_repository.flowers


@app.post("/flowers")
def post_flowers(flower: FlowerRequestResponse):
    flower = flowers_repository.add_flower(flower.name, flower.count, flower.cost)
    return {"flower_id": flower.id}

@app.post("/cart/items")
def post_cart_items(
    response: Response,
    flower_id: int = Form(),
    cart_items: str = Cookie(default="[]"),
):
    cart_items = json.loads(cart_items)
    cart_items.append(flower_id)
    cart_items = json.dumps(cart_items)
    response.set_cookie(key="cart_items", value=cart_items)
    return {}

@app.get("/cart/items")
def get_cart_items(
    request: Request,
    cart_items: str = Cookie(default="[]"),
):
    cart_items = json.loads(cart_items)
    flowers = [flower for flower in flowers_repository.flowers if flower.id in cart_items]
    total_cost = sum(flower.cost for flower in flowers)
    d = {
        "flowers": [{"name": flower.name, "cost": flower.cost, "count": flower.count} for flower in flowers],
        "total_cost": total_cost
        }
    return d