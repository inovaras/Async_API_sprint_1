import asyncio

import pytest
from settings import test_settings

from testdata.data.person import one_person
from testdata.data.film import one_film, film_collections

"""
все граничные случаи по валидации данных;
поиск конкретной персоны;+
вывести все фильмы, в которых участвовала персона;+
поиск с учётом кеша в Redis.+
"""


@pytest.mark.parametrize(
    'query_data, expected_answer, es_film_data, es_person_data',
    [
        (
            # поиск конкретной персоны;
            {"person_id": "person_uuid"},
            {'status': 200, "person_id": "person_uuid"},
            one_film,
            one_person,
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_person_by_id(
    es_remove_data,
    make_get_request,
    es_write_data,
    es_film_data: list[dict],
    es_person_data: list[dict],
    query_data: dict,
    expected_answer: dict,
):
    await es_write_data(es_film_data, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING)
    await es_write_data(
        es_person_data, index=test_settings.ES_PERSON_INDEX, mapping=test_settings.ES_PERSON_INDEX_MAPPING
    )
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/persons/{query_data['person_id']}"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_film_data, index=test_settings.ES_FILM_INDEX)
    await es_remove_data(es_person_data, index=test_settings.ES_PERSON_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert body['id'] == expected_answer['person_id']


@pytest.mark.parametrize(
    'query_data, expected_answer, es_film_data,es_person_data',
    [
        (
            {"person_id": "person_uuid", 'page': 1, 'per_page': len(film_collections)},
            {'status': 200, 'count': len(film_collections)},
            film_collections,
            one_person,
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_person_films(
    es_remove_data,
    make_get_request,
    es_write_data,
    es_film_data: list[dict],
    es_person_data: list[dict],
    query_data: dict,
    expected_answer: dict,
):
    await es_write_data(es_film_data, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING)
    await es_write_data(
        es_person_data, index=test_settings.ES_PERSON_INDEX, mapping=test_settings.ES_PERSON_INDEX_MAPPING
    )
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/persons/{query_data['person_id']}/film"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_film_data, index=test_settings.ES_FILM_INDEX)
    await es_remove_data(es_person_data, index=test_settings.ES_PERSON_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert type(body) == list
    assert len(body) == expected_answer['count']


@pytest.mark.parametrize(
    'query_data, expected_answer, es_film_data,es_person_data',
    [
        (
            {'query': 'Lucas'},
            {'status': 200, 'count': 1, 'id': 'person_uuid'},
            one_film,
            one_person
        )
    ],
)
@pytest.mark.asyncio
async def test_search_person(
    es_remove_data,
    make_get_request,
    es_write_data,
    es_film_data: list[dict],
    es_person_data: list[dict],
    query_data: dict,
    expected_answer: dict,
):
    await es_write_data(es_film_data, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING)
    await es_write_data(
        es_person_data, index=test_settings.ES_PERSON_INDEX, mapping=test_settings.ES_PERSON_INDEX_MAPPING
    )
    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/persons/search/"
    body, headers, status = await make_get_request(url, query_data)

    await es_remove_data(es_film_data, index=test_settings.ES_FILM_INDEX)
    await es_remove_data(es_person_data, index=test_settings.ES_PERSON_INDEX)
    body, headers, status = await make_get_request(url, query_data)

    assert status == expected_answer['status']
    assert type(body) == list
    assert len(body) == expected_answer['count']
