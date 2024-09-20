import asyncio
import pytest_asyncio

pytest_plugins = [
    "es_fixtures",
    "redis_fixtures",
    "http_fixtures"
]


@pytest_asyncio.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
