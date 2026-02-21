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


class UserLogin(BaseModel):
    email : str
    password : str

    
class UserDetails(BaseModel):
    username : str
    email : str
    password : str
    age: int

    @classmethod
    def as_form(cls,username:str = Form(...),email:str = Form(...),password : str=Form(...),age:str=Form(...)):
        return cls(username=username, email=email, age=age, password=password)



def access_token(data:dict):
    to_encode = data.copy()

    # expire = datetime.datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return token


# def token_required(func):
#     @wraps(func)
#     async def wrapper(*args, **kwargs):
#         request : Request = kwargs.get("request")
#         auth = request.headers.get('Authorization')
        
#         if not auth:
#             raise HTTPException(401, "token missing")

#         token = auth.split(" ")[1]
#         try:
#             jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         except JWTError:
#             raise HTTPException(401, "Invalid token ")

#         return await func(*args, **kwargs)
#     return wrapper


# async def token_required(request: Request, db=Depends(getdb)):
#     auth = request.headers.get("Authorization")

#     if not auth:
#         raise HTTPException(status_code=401, detail="Token missing")

#     token = auth.split(" ")[1]

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_email = payload.get('email')

#         if user_email is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
        
#         current_user = db.register.find_one({"email":user_email})
#         return current_user
    
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")
    


async def token_required(request: Request, db=Depends(getdb)):
    auth = request.headers.get("Authorization")

    if not auth:
        raise HTTPException(status_code=401, detail="Token missing")

    token = auth.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    except JWTError:        
        raise HTTPException(status_code=401, detail="Invalid token")
    

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
async def get_users(request:Request, user: UserModel, db=Depends(getdb), _:None = Depends(token_required)):
    if not user:
        raise
    data = await request.json()
    result = {
        "username" : data['name'],
        "email" : data["email"],
        "age" : data["age"]
    }

    res = db.users.insert_one(result)
    result["_id"] = str(res.inserted_id)
    return {"result":"user has been created"}


@token_required
@app.post("/test")
async def get_user(request: Request):           
    data = await request.json()
    return {"result": data}


@token_required
@app.get("/get_api")
async def apps(request: Request):
    data = request.query_params.get("name")
    return {"result": data}


@app.put("/modify_user")
async def modify_user(request:Request, user_data:UserModel, current_user:None = Depends(token_required),db=Depends(getdb)):
    if not user_data:
        raise
    data = await request.json()
    if data:
        # user_email = data.get("email")
        # filtered_data = db.register.find_one({"email":_})
        # filtered_data['username'] = data.get('name')
        # filtered_data['age'] = data.get("age")
        user = db.register.find_one({"email":current_user["sub"]})
        db.register.update_one({"_id":user['_id']},
                               {"$set":{
                                   "username":data.get("name"),
                                   "age":data.get("age")
                               }})
        
        return {"status":200,"message":"User updated successfully"}
    


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )