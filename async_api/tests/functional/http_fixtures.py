import pytest_asyncio
import aiohttp

@pytest_asyncio.fixture(name='aiohttp_client', scope='session')
async def aiohttp_client():
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