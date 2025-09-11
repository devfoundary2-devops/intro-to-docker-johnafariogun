from fastapi import FastAPI, HTTPException
import redis
import psycopg2
from psycopg2 import OperationalError, Error
import os

app = FastAPI()

# Redis connection
try:
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    r.ping()  # test connection
except redis.RedisError as e:
    r = None
    print(f"⚠️ Redis connection failed: {e}")

# Database connection settings
DB_HOST = os.getenv("DB_HOST", "db")   # "db" is the service name from docker-compose
DB_NAME = os.getenv("POSTGRES_DB", "demo")
DB_USER = os.getenv("POSTGRES_USER", "demo")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "password")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_connection():
    """Create a new PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except OperationalError as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.post('/users')
def create_users():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT UNIQUE);")
        cur.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob') ON CONFLICT DO NOTHING;")
        conn.commit()
        return {"success": "ok"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.get("/users")
def get_users():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users;")
        rows = cur.fetchall()
        return {"users": rows}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.get("/cache/{key}")
def cache_get(key: str):
    if not r:
        raise HTTPException(status_code=500, detail="Redis is unavailable")
    try:
        val = r.get(key)
        return {"key": key, "value": val}
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

@app.post("/cache/{key}/{value}")
def cache_set(key: str, value: str):
    if not r:
        raise HTTPException(status_code=500, detail="Redis is unavailable")
    try:
        r.set(key, value)
        return {"status": "ok"}
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

@app.get("/")
def root():
    return {"message": "Hello from Bootcamp Day 3"}
