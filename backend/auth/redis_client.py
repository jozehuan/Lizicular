import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def get_redis():
    """Dependencia para obtener un cliente de Redis con gestión de ciclo de vida."""
    client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

def get_redis_client():
    """Para uso fuera de dependencias de FastAPI (ej. inicialización)."""
    return redis.from_url(REDIS_URL, decode_responses=True)
