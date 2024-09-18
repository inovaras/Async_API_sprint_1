import asyncio
import time
from elasticsearch import AsyncElasticsearch, Elasticsearch

# if __name__=='__main__':
#     es_client=Elasticsearch(hosts='http://test-elasticsearch:9200')
#     while True:
#         if es_client.ping():
#             break
#         time.sleep(1)

# try:
#     from settings import test_settings
# except ImportError:
#     from ..settings import test_settings
import logging

logging.basicConfig(level=logging.DEBUG)


async def wait_elastic():
    while True:
        try:
            try:
                client = AsyncElasticsearch(hosts="http://172.19.0.4:9200", verify_certs=False)
            except Exception as exc:
                logging.info("TRASH")
                time.sleep(1)
            if await client.ping():
                break

        except Exception as e:
            logging.info("NO ELASTIC CONNECT. w8 1 sec")
            time.sleep(1)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(wait_elastic())
    # asyncio.run(wait_elastic())
