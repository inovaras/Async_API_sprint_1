import asyncio
import logging
import time

from redis.asyncio import Redis

# если хочешь увидеть неудачные попытки подключения - раскомментируй логирование
# logging.basicConfig(level=logging.DEBUG)


async def wait_redis():
    redis_client = Redis(host="172.19.0.5", port=6379)
    while True:
        if await redis_client.ping():
            break
        time.sleep(3)


if __name__ == '__main__':
    asyncio.run(wait_redis())
