from fastapi import FastAPI, Depends, HTTPException, Request, status, Form
from pydantic import BaseModel, Field
from pymongo import MongoClient
import uvicorn 
import secrets
from jose import jwt , JWTError
from datetime import datetime , timedelta
from functools import wraps

app = FastAPI()

#mongodb://localhost:27017/cms 
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class GetDB:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/cms")
        self.db = self.client['CMS']


def getdb():
    db = GetDB()
    try:
        yield db.db
    finally:
        db.client.close()

class UserModel(BaseModel):
    name: str
    age : int
    email : str

class UserDetails(BaseModel):
    username : str
    email : str
    password : str
    age: int

class UserLogin(BaseModel):
    email : str
    password : str

    @classmethod
    def as_form(cls,username:str = Form(...),email:str = Form(...),password : str=Form(...),age:str=Form(...)):
        return cls(username=username, email=email, age=age, password=password)


def access_token(data:dict):
    to_encode = data.copy()

    expire = datetime.datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return token


def token_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request : Request = kwargs.get("request")
        auth = request.headers.get('Authorization')
        
        if not auth:
            raise HTTPException(401, "token missing")

        token = auth.split(" ")[1]
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(401, "Invalid token ")

        return await func(*args, **kwargs)
    return wrapper


@app.post("/login")
async def login(request:Request,user_login: UserLogin, db=Depends(getdb)):
    if not user_login:
        raise HTTPException(status_code=400, detail="Invalid Creditials")
    data = await request.json()
    user_email = data.get("email")
    password = data.get("password")

    user = db.register.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if password != user.get("password"):
        raise HTTPException(status_code=401, detail="Wrong password")

    token = access_token({'sub': user_email})

    return {"access_token": token, "token_type": "bearer"}



@app.post("/register")
async def register(user_details:UserDetails= Depends(UserDetails.as_form), db= Depends(getdb)):
    # data = await request.json()
    res = {
        "username": user_details.username,
        "email" : user_details.email,
        "password" : user_details.password,
        "age" : user_details.age
    }

    result = db.register.insert_one(res)
    print("id", str(result.inserted_id))
    res["_id"] = str(result.inserted_id)
    return {"result" : "User has been Successful Registered"}
    



@app.post('/create_user',status_code=status.HTTP_201_CREATED)
async def get_users(request:Request, user: UserModel, db=Depends(getdb)):
    if not user:
        raise
    data = await request.json()
    result = {
        "username" : data['user_name'],
        "email" : data["email"],
        "age" : data["age"]
    }

    res = db.users.insert_one(result)
    result["_id"] = str(res.inserted_id)
    return {"result":"user has been created"}


@token_required
@app.get("/getUser")
async def get_user(request: Request, db =Depends(getdb)):
    data = await request.json()






if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )