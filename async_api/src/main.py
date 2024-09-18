from contextlib import asynccontextmanager

from api.v1 import films, persons, genres
from core.config import settings
from db import elastic, redis
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis



@asynccontextmanager
async def lifespan(_: FastAPI):
    # TODO наличие соединения не проверяется
    redis.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    elastic.es = AsyncElasticsearch(hosts=[f"{settings.ELASTIC_SCHEMA}{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"])
    print("redis connection successful")
    print("elastic connection successful")
    yield
    await redis.redis.close()
    await elastic.es.close()
    print("redis disconnection successful")
    print("elastic disconnection successful")


app = FastAPI(
    lifespan=lifespan,
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=settings.PROJECT_NAME,
    # Адрес документации в красивом интерфейсе
    docs_url="/api/openapi",
    # Адрес документации в формате OpenAPI
    openapi_url="/api/openapi.json",
    # Можно сразу сделать небольшую оптимизацию сервиса
    # и заменить стандартный JSON-сериализатор на более шуструю версию, написанную на Rust
    default_response_class=ORJSONResponse,
)

# Подключаем роутер к серверу, указав префикс /v1/films
# Теги указываем для удобства навигации по документации
app.include_router(films.router, prefix="/api/v1/films", tags=["films"])
app.include_router(persons.router, prefix="/api/v1/persons", tags=["persons"])
app.include_router(genres.router, prefix="/api/v1/genres", tags=["genres"])
