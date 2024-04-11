import sqlite3
from contextlib import asynccontextmanager

DATABASE_CAR_MODELS = 'car_models.db'
DATABASE_USERS = 'users.db'

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

@asynccontextmanager
async def app_lifespan(app):
    create_tables_car_models()
    create_tables_users()
    yield
