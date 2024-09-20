import asyncio
import logging

import backoff
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

# если хочешь увидеть неудачные попытки подключения - раскомментируй логирование
logging.basicConfig(level=logging.DEBUG)


@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=(ConnectionError, TimeoutError),
    jitter=backoff.full_jitter,
    max_value=5,
)
async def wait_redis():
    client = Redis(host="172.19.0.5", port=6379)
    if await client.ping():
        logging.info("connect to redis")
        return
    logging.info("dont much connect to redis")


if __name__ == "__main__":
    asyncio.run(wait_redis())
