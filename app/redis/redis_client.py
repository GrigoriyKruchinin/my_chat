from redis import asyncio as aioredis
from app.config import settings

redis_url = settings.REDIS_URL
redis_client = aioredis.from_url(redis_url)
