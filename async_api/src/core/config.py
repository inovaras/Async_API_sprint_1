import os
from logging import config as logging_config

from dotenv import load_dotenv

from core.logger import LOGGING

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(dotenv_path=f"{BASE_DIR}/../../configs/.env")
# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv("PROJECT_NAME", "movies")

# Настройки Redis
REDIS_HOST = os.getenv("REDIS_HOST", "172.18.0.6")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Настройки Elasticsearch
ELASTIC_HOST = os.getenv("ELASTICSEARCH_HOST", "172.18.0.5")
ELASTIC_PORT = int(os.getenv("ELASTICSEARCH_PORT", 9200))
ELASTIC_SCHEMA = "http://"
FILM_CACHE_EXPIRE_IN_SECONDS = int(os.getenv("FILM_CACHE_EXPIRE_IN_SECONDS", 300))
PERSON_CACHE_EXPIRE_IN_SECONDS = int(os.getenv("PERSON_CACHE_EXPIRE_IN_SECONDS", 600))
GENRE_CACHE_EXPIRE_IN_SECONDS = int(os.getenv("GENRE_CACHE_EXPIRE_IN_SECONDS", 1200))