import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Конфиг с использованием Pydantic
class Settings(BaseSettings):
    # Название проекта
    PROJECT_NAME: str

    # Настройки Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # Настройки Elasticsearch
    ELASTICSEARCH_HOST: str
    ELASTICSEARCH_PORT: int
    ELASTIC_SCHEMA: str = "http://"

    SQL_ENGINE: str

    # Настройки кеширования
    FILM_CACHE_EXPIRE_IN_SECONDS: int
    PERSON_CACHE_EXPIRE_IN_SECONDS: int
    GENRE_CACHE_EXPIRE_IN_SECONDS: int

    LOG_LEVEL: str

    class Config:
        env_file = f"{BASE_DIR}/../../configs/.env"
        extra = "ignore"


# Инициализация настроек
settings = Settings()
