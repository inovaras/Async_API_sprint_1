import asyncio

import pytest
from settings import test_settings
from testdata.data.film import film_collections, one_film

"""
все граничные случаи по валидации данных;
поиск конкретного фильма;+
вывести все фильмы;+
поиск с учётом кеша в Redis.
"""


@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
            # вывести фильмы без указания параметров;
            {},
            {'status': 200, 'length': 50},
            film_collections,
        ),
        (
            # вывести все фильмы;
            {"per_page": 60},
            {'status': 200, 'length': 60},
            film_collections,
        ),
    ],
)
@pytest.mark.asyncio
async def test_film(
    make_get_request, es_remove_data, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict
):
    await es_write_data(es_data, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING)
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/films"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_data, index=test_settings.ES_FILM_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    if expected_answer.get('length'):
        assert len(body) == expected_answer['length']
    if expected_answer.get('body'):
        assert body == expected_answer['body']


@pytest.mark.parametrize(
    'query_data, expected_answer, es_film_data, es_genre_data',
    [
        (
            # поиск конкретного фильма;
            {'filter_by': 'title', 'query': "Star"},
            {'status': 200},
            one_film,
            [{"id": "1", "name": "Action"}],
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_film_by_id(
    make_get_request,
    es_remove_data,
    es_write_data,
    es_film_data: list[dict],
    es_genre_data: list[dict],
    query_data: dict,
    expected_answer: dict,
):
    await es_write_data(es_film_data, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING)
    await es_write_data(es_genre_data, index=test_settings.ES_GENRE_INDEX, mapping=test_settings.ES_GENRE_INDEX_MAPPING)
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/films/my_uuid"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_film_data, index=test_settings.ES_FILM_INDEX)
    await es_remove_data(es_genre_data, index=test_settings.ES_GENRE_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert type(body) == dict
    assert body['id'] == "my_uuid"
    assert 'Action' in [genre['name'] for genre in body['genres']]


@pytest.mark.parametrize(
    'query_data, expected_answer, es_film_data, es_genre_data',
    [
        (
            # поиск конкретного фильма;
            {'filter_by': 'title', 'query': "Star"},
            {'status': 200},
            one_film,
            [{"id": "1", "name": "Action"}],
        ),
    ],
    ids=["test_cache"],
)
@pytest.mark.asyncio
async def test_cache_by_id(
    make_get_request,
    es_remove_data,
    es_write_data,
    es_film_data: list[dict],
    es_genre_data: list[dict],
    query_data: dict,
    expected_answer: dict,
):
    await es_write_data(es_film_data, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING)
    await es_write_data(es_genre_data, index=test_settings.ES_GENRE_INDEX, mapping=test_settings.ES_GENRE_INDEX_MAPPING)
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/films/my_uuid"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_film_data, index=test_settings.ES_FILM_INDEX)
    await es_remove_data(es_genre_data, index=test_settings.ES_GENRE_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert body is not None
