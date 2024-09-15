import asyncio

import pytest
from settings import test_settings

from testdata.data.film import film_collections, one_film

"""
все граничные случаи по валидации данных;
поиск конкретного фильма;+
вывести все фильмы;
поиск с учётом кеша в Redis.
"""

@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
                # вывести фильмы без указания параметров;
                {},
                {'status': 200, 'length': 50},
                film_collections
        ),
                (
                # вывести все фильмы;
                {"per_page":60},
                {'status': 200, 'length': 60},
                film_collections
        ),
    ]
)
@pytest.mark.asyncio
async def test_film(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):
    bulk_query: list[dict] = []
    for row in es_data:
        data = {"_index": test_settings.ES_FILM_INDEX, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    await es_write_data(bulk_query, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING )

    await asyncio.sleep(1)
    url = f"{test_settings.SERVICE_URL}/api/v1/films"
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    if expected_answer.get('length'):
        assert len(body) == expected_answer['length']
    if expected_answer.get('body'):
        assert body == expected_answer['body']

@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
            # поиск конкретного фильма;
                {'filter_by': 'title', 'query':"Star"},
                {'status': 200},
                one_film
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_film_by_id(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):
    bulk_query: list[dict] = []
    for row in es_data:
        data = {"_index": test_settings.ES_FILM_INDEX, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    await es_write_data(bulk_query, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING )
    await es_write_data(bulk_query, index=test_settings.ES_GENRE_INDEX, mapping=test_settings.ES_GENRE_INDEX_MAPPING)

    await asyncio.sleep(1)
    url = f"{test_settings.SERVICE_URL}/api/v1/films/my_uuid"
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert type(body) == dict
    assert body['id'] == "my_uuid"