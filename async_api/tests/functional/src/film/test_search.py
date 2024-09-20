import asyncio
import uuid
from http import HTTPStatus

import pytest
from plugins import pytest_plugins
from settings import test_settings
from testdata.data.film import film_collections

#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.


"""
    все граничные случаи по валидации данных;
    вывести только N записей;+
    поиск записи или записей по фразе;+
    поиск с учётом кеша в Redis.
"""


@pytest.mark.parametrize(
    "query_data, expected_answer, es_data",
    [
        (
            # поиск записи или записей по фразе
            # {'search': 'The Star'},
            {"query": "The Star"},
            {"status": HTTPStatus.OK, "length": 50},
            film_collections,
        ),
        (  # поиск не существующего фильма
            {"query": "Mashed potato"},
            {"status": HTTPStatus.NOT_FOUND, "body": {"detail": "Films not found"}},
            film_collections,
        ),
        (
            # вывести только N записей
            {"query": "The Star", "per_page": 1},
            {"status": HTTPStatus.OK, "length": 1},
            film_collections,
        ),
    ],
)
@pytest.mark.asyncio
async def test_search(
    make_get_request,
    es_remove_data,
    es_write_data,
    es_data: list[dict],
    query_data: dict,
    expected_answer: dict,
):
    # 2. Загружаем данные в ES
    await es_write_data(
        es_data,
        index=test_settings.ES_FILM_INDEX,
        mapping=test_settings.ES_FILM_INDEX_MAPPING,
    )

    # 3. Запрашиваем данные из ES по API
    url = f"{test_settings.SERVICE_URL}/api/v1/films/search"
    body, headers, status = await make_get_request(url, query_data)

    # Проверяем данные в кэшэ
    await es_remove_data(es_data, index=test_settings.ES_FILM_INDEX)
    body, headers, status = await make_get_request(url, query_data)
    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    if expected_answer.get("length"):
        assert len(body) == expected_answer["length"]
    if expected_answer.get("body"):
        assert body == expected_answer["body"]
