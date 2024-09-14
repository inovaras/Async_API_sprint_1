import os

from testdata.es_mapping.film import mapping as film_mapping
from testdata.es_mapping.genre import mapping as genre_mapping
from testdata.es_mapping.person import mapping as person_mapping
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestSettings(BaseSettings):
    # Название проекта
    PROJECT_NAME: str

    # Настройки Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # Настройки Elasticsearch
    ELASTICSEARCH_URL: str
    SQL_ENGINE: str

    # Настройки кеширования
    FILM_CACHE_EXPIRE_IN_SECONDS: int
    PERSON_CACHE_EXPIRE_IN_SECONDS: int
    GENRE_CACHE_EXPIRE_IN_SECONDS: int

    LOG_LEVEL: str

    ES_FILM_INDEX: str
    ES_GENRE_INDEX: str
    ES_PERSON_INDEX: str
    SERVICE_URL: str
    ES_FILM_INDEX_MAPPING: dict = film_mapping
    ES_GENRE_INDEX_MAPPING: dict = genre_mapping
    ES_PERSON_INDEX_MAPPING: dict = person_mapping

    class Config:
        env_file = f'{BASE_DIR}/functional/.env'
        extra = "ignore"


test_settings = TestSettings()
print()
