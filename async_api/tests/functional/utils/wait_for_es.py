import asyncio
import logging
import time

from elasticsearch import AsyncElasticsearch

# если хочешь увидеть неудачные попытки подключения - раскомментируй логирование
# logging.basicConfig(level=logging.DEBUG)


async def wait_elastic():
    client = AsyncElasticsearch(hosts="http://172.19.0.4:9200", verify_certs=False)
    while True:
        if await client.ping():
            break
        time.sleep(10)


if __name__ == '__main__':
    asyncio.run(wait_elastic())
