import asyncio

import aiohttp
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from redis.asyncio import Redis
from settings import test_settings


@pytest_asyncio.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name='es_client', scope='session')
async def es_client():
    es_client = AsyncElasticsearch(hosts=test_settings.ELASTICSEARCH_URL, verify_certs=False)
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(autouse=True)
async def redis_client():
    yield
    redis = Redis(host=test_settings.REDIS_HOST, port=test_settings.REDIS_PORT)
    await redis.flushall()
    await redis.aclose()


@pytest_asyncio.fixture(name='es_write_data')
def es_write_data(es_client: AsyncElasticsearch):
    async def inner(data: list[dict], index: str, mapping: dict):
        if await es_client.indices.exists(index=index):
            await es_client.indices.delete(index=index)
        await es_client.indices.create(index=index, **mapping)

        bulk_data: list[dict] = []
        for row in data:
            data_to_es = {"_index": index, "_id": row["id"]}
            data_to_es.update({"_source": row})
            bulk_data.append(data_to_es)

        updated, errors = await async_bulk(client=es_client, actions=bulk_data)
        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')

    return inner


@pytest_asyncio.fixture(name='es_remove_data')
def es_remove_data(es_client: AsyncElasticsearch):
    async def inner(data: list[dict], index: str):
        for info in data:
            await es_client.delete(index=index, id=info["id"])

    return inner


@pytest_asyncio.fixture(name='aiohttp_client', scope='session')
async def aiohttp_client():
    # client = aiohttp.ClientSession()
    # yield client
    # await client.close()

    async with aiohttp.ClientSession() as session:
        yield session


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request(aiohttp_client: aiohttp.ClientSession):
    async def inner(url: str, query_data: dict):
        response = await aiohttp_client.get(url=url, params=query_data)
        body = await response.json()
        headers = response.headers
        status = response.status
        return body, headers, status

    return inner
