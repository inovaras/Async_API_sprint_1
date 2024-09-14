import asyncio
import uuid

import pytest
from settings import test_settings

#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.

@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                # {'search': 'The Star'},
                {'query': 'The Star'},
                {'status': 200, 'length': 50}
        ),
        (
                {'query': 'Mashed potato'},
                {'status': 404, "body": {'detail': 'Films not found'}}
        )
    ]
)
@pytest.mark.asyncio
# async def test_search(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):
async def test_search(make_get_request, es_write_data, query_data: dict, expected_answer: dict):

    # 1. Генерируем данные для ES
    es_data = [
        {
            "id": str(uuid.uuid4()),
            "imdb_rating": 8.5,
            "genres": ["Action", "Sci-Fi"],
            "title": "Star",
            "description": "New World",
            "directors": [{"id": "a5a8f573-3cee-4ccc-8a2b-91cb9f55250a", "name": "George Lucas"}],
            "actors": [
                {"id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95", "name": "Ann"},
                {"id": "fb111f22-121e-44a7-b78f-b19191810fbf", "name": "Bob"},
            ],
            "writers": [
                {"id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5", "name": "Ben"},
                {"id": "b45bd7bc-2e16-46d5-b125-983d356768c6", "name": "Howard"},
            ],
            "directors_names": ["George Lucas"],
            "actors_names": ["Ann", "Bob"],
            "writers_names": ["Ben", "Howard"],
            # "created_at": datetime.datetime.now().isoformat(),
            # "updated_at": datetime.datetime.now().isoformat(),
        }
        for _ in range(60)
    ]

    bulk_query: list[dict] = []
    for row in es_data:
        data = {"_index": test_settings.ES_FILM_INDEX, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # ждем обработки данных elastic
    await asyncio.sleep(1)

    # 3. Запрашиваем данные из ES по API
    # query_data = {"query": "The Star"}
    url = f"{test_settings.SERVICE_URL}/api/v1/films/search/"
    body, headers, status = await make_get_request(url, query_data)

    # 4. Проверяем ответ
    assert status == expected_answer['status']
    if expected_answer.get('length'):
        assert len(body) == expected_answer['length']
    if expected_answer.get('body'):
        assert body == expected_answer['body']
