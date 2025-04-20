from fastapi import FastAPI, HTTPException
import redis
import os

app = FastAPI()

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 1))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    r.ping()  # Test connection
    print("Connected to Redis")
except redis.RedisError as e:
    print("Redis connection failed:", str(e))
    r = None