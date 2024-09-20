import pytest_asyncio
from redis.asyncio import Redis
from settings import test_settings

@pytest_asyncio.fixture(autouse=True)
async def redis_client():
    yield
    redis = Redis(host=test_settings.REDIS_HOST, port=test_settings.REDIS_PORT)
    await redis.flushall()
    await redis.aclose()
