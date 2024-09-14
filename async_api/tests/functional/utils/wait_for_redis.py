import time
from redis.asyncio import Redis

if __name__=='__main__':
    redis_client=Redis(host='http://test-redis:6379')
    while True:
        if redis_client.ping():
            break
        time.sleep(1)