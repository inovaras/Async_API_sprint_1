import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from settings import test_settings

@pytest_asyncio.fixture(name='es_client', scope='session')
async def es_client():
    es_client = AsyncElasticsearch(hosts=test_settings.ELASTICSEARCH_URL, verify_certs=False)
    yield es_client
    await es_client.close()

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