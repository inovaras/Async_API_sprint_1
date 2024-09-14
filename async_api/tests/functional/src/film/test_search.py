import asyncio
import uuid

import pytest
from settings import test_settings

from testdata.data.film import film_collections
#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.


"""
    все граничные случаи по валидации данных;
    вывести только N записей;
    поиск записи или записей по фразе;
    поиск с учётом кеша в Redis.
"""

"""
{'query': 'The Star', "per_page": 1, "page":1}, # BUG если не указать page код падает.
{'status': 200, 'length': 1}
File "/async_api/src/services/base.py", line 103, in _get_correct_params
    query_params["offset"] = (query_params["page"] - 1) * query_params["per_page"]
"""


@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
                # {'search': 'The Star'},
                {'query': 'The Star'},
                {'status': 200, 'length': 50},
                film_collections
        ),
        (
                {'query': 'Mashed potato'},
                {'status': 404, "body": {'detail': 'Films not found'}},
                film_collections
        ),
                (
                # вывести только N записей
                {'query': 'The Star', "per_page": 1, "page":1}, # BUG если не указать page код падает.
                {'status': 200, 'length': 1},
                film_collections
        ),
    ]
)
@pytest.mark.asyncio
async def test_search(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):

    bulk_query: list[dict] = []
    for row in es_data:
        data = {"_index": test_settings.ES_FILM_INDEX, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING )

    # ждем обработки данных elastic
    await asyncio.sleep(1)

    # 3. Запрашиваем данные из ES по API
    url = f"{test_settings.SERVICE_URL}/api/v1/films/search/"
    body, headers, status = await make_get_request(url, query_data)

    # 4. Проверяем ответ
    assert status == expected_answer['status']
    if expected_answer.get('length'):
        assert len(body) == expected_answer['length']
    if expected_answer.get('body'):
        assert body == expected_answer['body']
