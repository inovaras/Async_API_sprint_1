import os
from unittest.util import strclass

from pydantic import Field
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
    ES_FILM_INDEX_MAPPING: dict = {
        "settings": {
            "refresh_interval": "1s",
            "analysis": {
                "filter": {
                    "english_stop": {"type": "stop", "stopwords": "_english_"},
                    "english_stemmer": {"type": "stemmer", "language": "english"},
                    "english_possessive_stemmer": {"type": "stemmer", "language": "possessive_english"},
                    "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                    "russian_stemmer": {"type": "stemmer", "language": "russian"},
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "english_stemmer",
                            "english_possessive_stemmer",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    }
                },
            },
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "imdb_rating": {"type": "float"},
                "genres": {"type": "text"},
                "title": {"type": "text", "analyzer": "ru_en", "fields": {"raw": {"type": "keyword"}}},
                "description": {"type": "text", "analyzer": "ru_en"},
                "directors_names": {"type": "text", "analyzer": "ru_en"},
                "actors_names": {"type": "text", "analyzer": "ru_en"},
                "writers_names": {"type": "text", "analyzer": "ru_en"},
                "directors": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {"id": {"type": "keyword"}, "name": {"type": "text", "analyzer": "ru_en"}},
                },
                "actors": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {"id": {"type": "keyword"}, "name": {"type": "text", "analyzer": "ru_en"}},
                },
                "writers": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {"id": {"type": "keyword"}, "name": {"type": "text", "analyzer": "ru_en"}},
                },
            },
        },
    }

    class Config:
        env_file = f'{BASE_DIR}/functional/.env'
        extra = "ignore"


test_settings = TestSettings()
print()
