import os
from pydantic_settings import BaseSettings


from dotenv import load_dotenv

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
        # env_file = "../../configs/.env"
        env_file = f"{BASE_DIR}/../../configs/.env"
        extra = "ignore"

    # model_config = SettingsConfigDict(env_file='.env', extra='ignore')

# Инициализация настроек
settings = Settings()


# проверка
# print(f"Project Name: {settings.project_name}")
# print(f"Redis Host: {settings.redis_host}")
# print(f"Redis Port: {settings.redis_port}")