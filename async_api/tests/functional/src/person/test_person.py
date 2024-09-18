import asyncio

import pytest
from settings import test_settings

from testdata.data.person import  one_person

"""
все граничные случаи по валидации данных;
поиск конкретной персоны;
вывести все фильмы, в которых участвовала персона;
поиск с учётом кеша в Redis.
"""


@pytest.mark.parametrize(
    'query_data, expected_answer, es_data',
    [
        (
            # поиск конкретной персоны;
            {"id": "my_uuid"},
            {'status': 200},
            one_person
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_person_by_id(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):
    persons: list[dict] = []
    for row in es_data:
        data = {"_index": test_settings.ES_PERSON_INDEX, "_id": row["id"]}
        data.update({"_source": row})
        persons.append(data)

    await es_write_data(persons, index=test_settings.ES_PERSON_INDEX, mapping=test_settings.ES_PERSON_INDEX_MAPPING)

    await asyncio.sleep(1)

    url = f"{test_settings.SERVICE_URL}/api/v1/persons/my_uuid"
    body, headers, status = await make_get_request(url, {})


    assert status == expected_answer['status']
    assert body['id'] == expected_answer['id']
    # assert body['id'] == expected_answer['id']
    # assert body['full_name'] == expected_answer['full_name']

# @pytest.mark.parametrize(
#     'person_id, query_data, expected_answer, es_data',
#     [
#         (
#             {'person_id'},
#             {'page': 1, 'per_page': 50},
#             {'status': 200, 'count': 1, 'id': 'my_uuid', 'title': 'film1'},
#             [one_person]
#         ),
#     ]
# )
# @pytest.mark.asyncio
# async def test_get_person_films(make_get_request, es_write_data, es_data: list[dict], person_id: str, query_data: dict, expected_answer: dict):
#     persons: list[dict] = []
#     for row in es_data:
#         data = {"_index": test_settings.ES_FILM_INDEX, "_id": row["id"]}
#         data.update({"_source": row})
#         persons.append(data)

#     await es_write_data(persons, index=test_settings.ES_FILM_INDEX, mapping=test_settings.ES_FILM_INDEX_MAPPING)

#     await asyncio.sleep(1)

#     url = f"{test_settings.SERVICE_URL}/api/v1/persons/{person_id}/film"
#     body, headers, status = await make_get_request(url, query_data)

#     assert status == expected_answer['status']
#     assert type(body) == list
#     assert len(body) == expected_answer['count']
#     assert body[0]['id'] == expected_answer['id']
#     assert body[0]['title'] == expected_answer['title']


# @pytest.mark.parametrize(
#     'query_data, expected_answer, es_data',
#     [
#         (
#             {'query': 'Star', 'page': 1, 'per_page': 50},
#             {'status': 200, 'count': 1, 'id': 'person_uuid', 'title': 'Some Title'},
#             one_person
#         ),
#     ]
# )
# @pytest.mark.asyncio
# async def test_search_person(make_get_request, es_write_data, es_data: list[dict], query_data: dict, expected_answer: dict):
#     bulk_query: list[dict] = []
#     for row in es_data:
#         data = {"_index": test_settings.ES_PERSON_INDEX, "_id": row["id"]}
#         data.update({"_source": row})
#         bulk_query.append(data)

#     await es_write_data(bulk_query, index=test_settings.ES_PERSON_INDEX, mapping=test_settings.ES_PERSON_INDEX_MAPPING)

#     await asyncio.sleep(1)

#     url = f"{test_settings.SERVICE_URL}/api/v1/persons/search/"
#     body, headers, status = await make_get_request(url, query_data)

#     assert status == expected_answer['status']
#     assert type(body) == list
#     assert len(body) == expected_answer['count']
#     assert body[0]['id'] == expected_answer['id']
#     assert body[0]['title'] == expected_answer['title']
