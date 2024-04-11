from contextlib import asynccontextmanager
from faker import Faker
from typing import Optional, Union
import random
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
from jose import JWTError, jwt
from passlib.context import CryptContext
from os import makedirs


# Config
DATABASE_CAR_MODELS = 'car_models.db'
DATABASE_USERS = 'users.db'
IMAGE_DIR = 'uploaded_images'
makedirs(IMAGE_DIR, exist_ok=True)
fake = Faker()

SECRET_KEY = "c1591e1c961c5da73be50b329c8390a2ec7d38c3e5615152ec10f4c0202fbaa4"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Pydantic models
class CarModel(BaseModel):
    manufacturer: str
    model: str
    year: int
    price: float


class CarModelInDB(CarModel):
    id: int


# Database functions
def get_db_connection(db_filename):
    conn = sqlite3.connect(db_filename)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables_car_models():
    conn = get_db_connection(DATABASE_CAR_MODELS)
    conn.execute('''CREATE TABLE IF NOT EXISTS car_models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        manufacturer TEXT NOT NULL,
                        model TEXT NOT NULL,
                        year INTEGER NOT NULL,
                        price REAL NOT NULL,
                        image_path TEXT)''')
    conn.commit()
    conn.close()


def create_tables_users():
    conn = get_db_connection(DATABASE_USERS)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL,
                        full_name TEXT,
                        hashed_password TEXT NOT NULL,
                        disabled INTEGER NOT NULL DEFAULT 0)''')
    conn.commit()
    conn.close()


# Handle db creation if it doesn't exist on startup (as on_event was deprecated)
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Run startup code here
    create_tables_car_models()
    create_tables_users()
    yield
    # Run shutdown code here


# User models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated='auto')
oath2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(lifespan=app_lifespan)

# User authentication functions
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    conn = get_db_connection(DATABASE_USERS)
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if username:
        return UserInDB(**user)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# User authentication routes
async def get_current_user(token: str = Depends(oath2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials",
                                         headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credential_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# User authentication routes
@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Incorrect username or password",
                            headers={'WWW-Authenticate':"Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Redirecting to docs route
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs", status_code=301)

# Car model routes
@app.get("/car_models/", response_model=list[CarModelInDB])
async def read_car_models(limit: int = 10,
                        sort_by: Optional[str] = Query(None, enum=["id", "manufacturer", "model", "year", "price"]),
                        descending: Optional[bool] = Query(None, enum=[True, False]),
                        current_user: User = Depends(get_current_active_user)):
    conn = get_db_connection(DATABASE_CAR_MODELS)

    base_query = "SELECT * FROM car_models"
    order_clause = f" ORDER BY {sort_by} {'DESC' if descending else 'ASC'}" if sort_by else ""
    final_query = f"{base_query}{order_clause} LIMIT ?"

    car_models = conn.execute(final_query, (limit,)).fetchall()    
    conn.close()
    # Convert the rows to dict
    car_models_list = [dict(model) for model in car_models]
    return [CarModelInDB(**model) for model in car_models_list]


@app.post("/car_models/", response_model=CarModelInDB)
async def create_car_model(car_model: CarModel, current_user: User = Depends(get_current_active_user)):
    conn = get_db_connection(DATABASE_CAR_MODELS)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO car_models (manufacturer, model, year, price)
                      VALUES (?, ?, ?, ?)''',
                   (car_model.manufacturer, car_model.model, car_model.year, car_model.price))
    car_model_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {**car_model.dict(), "id": car_model_id}


@app.get("/car_models/{car_model_id}", response_model=CarModelInDB)
async def read_car_model(car_model_id: int, current_user: User = Depends(get_current_active_user)):
    conn = get_db_connection(DATABASE_CAR_MODELS)
    car_model = conn.execute('SELECT * FROM car_models WHERE id = ?', (car_model_id,)).fetchone()
    conn.close()
    if car_model is None:
        raise HTTPException(status_code=404, detail=fr"CarModel with id: '{car_model_id}' was not found")
    return dict(car_model)


@app.put("/car_models/{car_model_id}", response_model=CarModelInDB)
async def update_car_model(car_model_id: int, car_model: CarModel, current_user: User = Depends(get_current_active_user)):
    conn = get_db_connection(DATABASE_CAR_MODELS)
    cursor = conn.cursor()
    cursor.execute('''UPDATE car_models
                      SET manufacturer = ?, model = ?, year = ?, price = ?
                      WHERE id = ?''',
                   (car_model.manufacturer, car_model.model, car_model.year, car_model.price, car_model_id))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="CarModel not found")
    conn.close()
    return {**car_model.model_dump(), "id": car_model_id}


@app.delete("/car_models/{car_model_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_car_model(car_model_id: int, current_user: User = Depends(get_current_active_user)):
    conn = get_db_connection(DATABASE_CAR_MODELS)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM car_models WHERE id = ?', (car_model_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CarModel not found")
    conn.close()
    return {"ok": True}


@app.post("/car_models/{car_model_id}/image/", status_code=status.HTTP_201_CREATED)
async def upload_car_model_image(car_model_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    file_location = f"{IMAGE_DIR}/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    conn = get_db_connection(DATABASE_CAR_MODELS)
    cursor = conn.cursor()
    cursor.execute('UPDATE car_models SET image_path = ? WHERE id = ?', (file_location, car_model_id))
    conn.commit()
    conn.close()
    return {"info": f"image of Car Model id:'{car_model_id}' was set to '{file.filename}'"}


@app.put("/car_models/{car_model_id}/image/", status_code=status.HTTP_202_ACCEPTED)
async def update_car_model_image(car_model_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    file_location = f"{IMAGE_DIR}/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    conn = get_db_connection(DATABASE_CAR_MODELS)
    cursor = conn.cursor()
    cursor.execute('''UPDATE car_models
                      SET image_path = ? 
                      WHERE id = ?''',
                   (file_location, car_model_id))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="CarModel not found")
    conn.close()
    return {"info": f"image of Car Model id:'{car_model_id}' was updated to '{file.filename}'"}


@app.delete("/car_models/{car_model_id}/image/", status_code=status.HTTP_202_ACCEPTED)
async def delete_car_model_image(car_model_id: int, current_user: User = Depends(get_current_active_user)):
    conn = get_db_connection(DATABASE_CAR_MODELS)
    cursor = conn.cursor()
    cursor.execute("UPDATE car_models SET image_path = NULL WHERE id = ?", (car_model_id,))
    conn.commit()
    conn.close()
    return {"info": fr"Deleted image link on model id: {car_model_id}"}


def create_random_car_model():
    # Generate random data for a car model
    manufacturer = fake.company()
    model = fake.word()
    year = random.randint(1990, 2021)
    price = round(random.uniform(5000, 70000), 2)

    return manufacturer, model, year, price


def insert_random_car_models(n):
    conn = get_db_connection(DATABASE_CAR_MODELS)
    cursor = conn.cursor()
    for _ in range(n):
        car_model_data = create_random_car_model()
        cursor.execute('''
            INSERT INTO car_models (manufacturer, model, year, price)
            VALUES (?, ?, ?, ?)
        ''', car_model_data)
    conn.commit()
    conn.close()


def add_user_to_database(username, email, password):
    hashed_password = get_password_hash(password)
    conn = get_db_connection(DATABASE_USERS)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (username, email, hashed_password)
                      VALUES (?, ?, ?)''', (username, email, hashed_password))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    #insert_random_car_models(n = 10)  # Insert 10 random car models
    #add_user_to_database("admin", "example@example.com", "admin123")
    pass
