import asyncio
import pytest
from http import HTTPStatus

from settings import test_settings
from testdata.data.genre import one_genre, genres

"""
все граничные случаи по валидации данных;
поиск конкретного жанра;
вывести все фильмы;
поиск с учётом кеша в Redis.
"""


@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
            # поиск конкретного жанра;
            {'genre_id': "my_uuid"},
            {'status': HTTPStatus.OK},
            one_genre,
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_genre_by_id(
    es_remove_data, make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict
):
    await es_write_data(es_data, index=test_settings.ES_GENRE_INDEX, mapping=test_settings.ES_GENRE_INDEX_MAPPING)
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/genres/{query_data['genre_id']}"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_data, index=test_settings.ES_GENRE_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert type(body) == dict
    assert body['id'] == "my_uuid"


@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
            # поиск жанров;
            {},
            {'status': HTTPStatus.OK, 'length': 3},
            genres,
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_genres(
    es_remove_data, make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict
):
    await es_write_data(es_data, index=test_settings.ES_GENRE_INDEX, mapping=test_settings.ES_GENRE_INDEX_MAPPING)
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/genres"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_data, index=test_settings.ES_GENRE_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert len(body) == expected_answer['length']
    assert type(body) == list
