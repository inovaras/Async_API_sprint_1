import asyncio
import backoff

import logging
import time

from elasticsearch import AsyncElasticsearch
from elastic_transport import ConnectionError, ConnectionTimeout

# если хочешь увидеть неудачные попытки подключения - раскомментируй логирование
logging.basicConfig(level=logging.DEBUG)

# BUG AsyncElasticsearch and Elasticsearch ignore all exceptions and dont worked. USE asyncio.sleep(30)
# @backoff.on_exception(
#     wait_gen=backoff.expo,
#     # exception=(ConnectionError, ConnectionTimeout),
#     exception=(Exception),
#     jitter=backoff.full_jitter,
#     max_value=5,
# )
# async def wait_elastic():
#     client = AsyncElasticsearch(hosts="http://172.19.0.4:9200", verify_certs=False)
#     if await client.ping():
#         logging.info("connect to elastic")
#         return
#     # await asyncio.sleep(30)
#     logging.info("dont much connect to elastic")

async def wait_elastic():
    while True:
        client = AsyncElasticsearch(hosts="http://172.19.0.4:9200", verify_certs=False)
        if await client.ping():
            logging.info("connect to elastic")
            break
        logging.info("dont much connect to elastic")
        await asyncio.sleep(30)


if __name__ == '__main__':
    asyncio.run(wait_elastic())
