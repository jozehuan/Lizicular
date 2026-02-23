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

class RedisClientManager:
    """Para uso fuera de dependencias de FastAPI (ej. inicialización)."""
    
    def __init__(self):
        self.client = None
    
    async def __aenter__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
