import asyncio

import aiohttp
from settings import test_settings
from elasticsearch import AsyncElasticsearch
import pytest_asyncio
from elasticsearch.helpers import async_bulk


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


@pytest_asyncio.fixture(name='es_write_data')
def es_write_data(es_client: AsyncElasticsearch):
    async def inner(data: list[dict], index:str,mapping:dict):
        if await es_client.indices.exists(index=index):
            await es_client.indices.delete(index=index)
        await es_client.indices.create(index=index, **mapping)
        updated, errors = await async_bulk(client=es_client, actions=data)
        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')


        # if await es_client.indices.exists(index=test_settings.ES_FILM_INDEX):
        #     await es_client.indices.delete(index=test_settings.ES_FILM_INDEX)
        # await es_client.indices.create(index=test_settings.ES_FILM_INDEX, **test_settings.ES_FILM_INDEX_MAPPING)
        # updated, errors = await async_bulk(client=es_client, actions=data)
        # if errors:
        #     raise Exception('Ошибка записи данных в Elasticsearch')

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
    async def inner(url:str, query_data:dict):
        response = await aiohttp_client.get(url=url, params=query_data)
        body = await response.json()
        headers = response.headers
        status = response.status
        return body, headers, status

    return inner