import asyncio

import pytest
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
                {'genre_id':"my_uuid"},
                {'status': 200},
                one_genre
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_genre_by_id(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):
    genres: list[dict] = []
    for row in es_data:
        data = {"_index": test_settings.ES_GENRE_INDEX, "_id": row["id"]}
        data.update({"_source": row})
        genres.append(data)

    # await es_write_data(bulk_query, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING )
    await es_write_data(genres, index=test_settings.ES_GENRE_INDEX, mapping=test_settings.ES_GENRE_INDEX_MAPPING)

    await asyncio.sleep(1)
    url = f"{test_settings.SERVICE_URL}/api/v1/genres/my_uuid"
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert type(body) == dict
    assert body['id'] == "my_uuid"


@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
            # поиск жанров;
                {}, {'status': 200, 'length': 3}, genres
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_genres(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):
    genres: list[dict] = []
    for row in es_data:
        data = {"_index": test_settings.ES_GENRE_INDEX, "_id": row["id"]}
        data.update({"_source": row})
        genres.append(data)

    # await es_write_data(bulk_query, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING )
    await es_write_data(genres, index=test_settings.ES_GENRE_INDEX, mapping=test_settings.ES_GENRE_INDEX_MAPPING)

    await asyncio.sleep(2)
    url = f"{test_settings.SERVICE_URL}/api/v1/genres"
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert len(body) == expected_answer['length']
    assert type(body) == list
