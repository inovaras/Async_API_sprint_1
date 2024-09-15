import time
from redis import Redis
# from settings import test_settings
import logging

logging.basicConfig(level=logging.DEBUG)

def wait_redis():
    redis_client=Redis(host="http://172.19.0.5", port=6379)
    while True:
        try:
            if redis_client.ping():
                break

        except Exception:
            logging.info("NO REDIS CONNECT. w8 1 sec")
            time.sleep(1)

if __name__=='__main__':
    wait_redis()