# Проектная работа 4 спринта

**Важное сообщение для тимлида:** для ускорения проверки проекта укажите ссылку на приватный репозиторий с командной работой в файле readme и отправьте свежее приглашение на аккаунт [BlueDeep](https://github.com/BigDeepBlue).

В папке **tasks** ваша команда найдёт задачи, которые необходимо выполнить в первом спринте второго модуля.  Обратите внимание на задачи **00_create_repo** и **01_create_basis**. Они расцениваются как блокирующие для командной работы, поэтому их необходимо выполнить как можно раньше.

Мы оценили задачи в стори поинтах, значения которых брались из [последовательности Фибоначчи](https://ru.wikipedia.org/wiki/Числа_Фибоначчи) (1,2,3,5,8,…).

Вы можете разбить имеющиеся задачи на более маленькие, например, распределять между участниками команды не большие куски задания, а маленькие подзадачи. В таком случае не забудьте зафиксировать изменения в issues в репозитории.

**От каждого разработчика ожидается выполнение минимум 40% от общего числа стори поинтов в спринте.**

# Ревьюеру - [Ссылка на приватный репозиторий](https://github.com/NankuF/Async_API_sprint_1)

# Readonly асинхронный API с кэшированием и поиском в Elasticsearch


## Требования перед  установкой
1) Linux (проект разработан на Ubuntu 22.04.4 LTS)
2) python >= 3.10
3) Docker

Скачать репозиторий и перейти в него.
```bash
git clone git@github.com:NankuF/Async_API_sprint_1.git && cd ./Async_API_sprint_1
```
Переименовать `.env.example` в `.env`
```bash
cp ./configs/.env.example ./configs/.env
```
В директории с репозиторием выполнить скрипт, разворачивающий сеть и volumes.
```bash
docker compose down &&\
docker volume rm theatre-db-data &&\
docker volume rm elasticsearch-data &&\
docker volume rm redis-cache &&\
docker volume rm admin-static &&\
docker volume rm admin-media &&\
docker network rm middle-practicum &&\
docker network create middle-practicum --subnet 172.18.0.0/24 --gateway 172.18.0.1 &&\
docker volume create theatre-db-data &&\
docker volume create elasticsearch-data &&\
docker volume create redis-cache &&\
docker volume create admin-static &&\
docker volume create admin-media
```

*Для dev-запуска необходимо закомментировать сервис `async-api` в `docker-compose.yml`*

Запустить docker compose (`docker-compose.yml` должен находиться в этой же директории)
```bash
docker compose up -d --build
```
Убедиться что etl-процессы отработали успешно. Перенесены фильмы, персоны и жанры в elasticsearch.
```bash
curl -XGET http://172.18.0.5:9200/_cat/indices?v
```
В колонке `docs.count` указано кол-во документов пересенных ETL-процессом.
```text
health status index   uuid                   pri rep docs.count docs.deleted store.size pri.store.size
yellow open   movies  FJsV8_apRj6sOfOMCVJ_XQ   1   1       6782            0      1.5mb          1.5mb
yellow open   persons SwhRqmCmSTOmhfD2uwAEyA   1   1       4166            0        1mb            1mb
yellow open   genres  bbZVj-KTSs6SLV1Nfl3OOg   1   1         26            0      9.7kb          9.7kb

```

## Общее
Проект разворачивается через docker compose.<br>
*Для dev-запуска необходимо закомментировать сервис `async-api` в `docker-compose.yml`.*<br>
Используется сеть со статичными адресами для устранения проблемы смены ip адресов при перезапуске контейнеров.<br>
Используются созданные вручную контейнеры для предотвращения потери данных.<br>

В проекте используется код из ранее выполненных спринтов, спринты загружены в виде образов на docker hub.<br>
[Админка](https://github.com/NankuF/new_admin_panel_sprint_2)
```yaml
  service:
    image: inovaras/admin-app
```
[ETL процесс](https://github.com/NankuF/new_admin_panel_sprint_3) обновления данных из postgres в elasticsearch при внесении изменений через админку.
```yaml
  admin-etl-process:
    image: inovaras/admin-etl
```

API из докера доступно по адресу: http://127.0.0.1:8080/api/openapi#/<br>
API при запуске в IDE доступно по адресу: http://127.0.0.1:8000/api/openapi#/<br>
Админ-панель доступна по адресу: http://127.0.0.1/admin/<br>
Login: `admin`<br>
Password: `123123`<br>

## Запуск в Docker
1) Выполнить "Требования перед  установкой".
2) Открыть API
```text
http://127.0.0.1:8080/api/openapi#/
```

## Запуск локально для разработки проекта
*Для dev-запуска необходимо закомментировать сервис `async-api` в `docker-compose.yml`*
1) Выполнить "Требования перед  установкой".
2) Установить виртуальное окружение и зависимости.
```bash
python3 -m venv venv && . ./venv/bin/activate && pip install -r requirements.txt && cd async_api/src/
```
3) Запустить приложение
```bash
fastapi dev main.py
```
4) Открыть API
```text
http://127.0.0.1:8000/api/openapi#/
```

## Ожидаемое поведение
- API собрано по [ТЗ](https://practicum.yandex.ru/learn/middle-python/courses/7c4e333e-2395-4f53-88af-256bc6aab346/sprints/231500/topics/7ee9e96e-c2e8-4a7b-9b5c-b626a91aa234/lessons/3d52a604-2fcd-4593-8f4b-065e8cb6af75/)
- Все эндпоинты кешируются по uuid, либо по составному ключу.
   - По uuid кэшируются запросы для одного объекта(персона, фильм, жанр).
   - По составному ключу кэшируются запросы для получения списка объектов.<br>
   - Поиск сначала производится в кэше, затем в elasticsearch. Ответ возвращается в API.<br>
В качествесоставного ключа используется строка вида `url.path?url.query`.<br>
## Redis
Класс реализующий кэширование находится в ```services.cache.cache.py```.<br>
Кэширование проверяется до запроса в elasticsearch.<br>
Кэш записывается после запроса в elasticsearch.<br>
Срок жизни кэша указан в `.env`:<br>
`FILM_CACHE_EXPIRE_IN_SECONDS=300`<br>
`PERSON_CACHE_EXPIRE_IN_SECONDS=300`<br>
`GENRE_CACHE_EXPIRE_IN_SECONDS=300`<br>

Кэширование используется в абстрактном сервисе `BaseService`, и его наследниках `FilmService`, `GenreService`, `PersonService`.<br>

## Elasticsearch
Поисковые запросы к elasticsearch формируются в методе `_build_query_request()`.<br>
Используется простое сравнение эндпоинта api c `url.path`.
Данные собираются из elasticsearch при помощи поисковых запросов.<br>
**Примеры:**<br>
Запрос для поиска id в любом из трех `List[dict]`. Используется в `person_films` для поиска роли по `uuid` в `directors`,
`writers` и `actors`.<br>
`should` - эквивалент OR.<br>
`path` - ключ в котором elastic хранит данные.<br>
`term` - тип соответствия. `term` - точное соответствие (идеально подходит для uuid).<br>
```python
{
"bool": {
    "should": [
        {"nested": {"path": "directors", "query": {"term": {"directors.id": person.id}}}},
        {"nested": {"path": "writers", "query": {"term": {"writers.id": person.id}}}},
        {"nested": {"path": "actors", "query": {"term": {"actors.id": person.id}}}},
    ]
    }
}
```
Поиск в сочетании по нескольким словам (фразовый поиск). Используется в `search_by_persons` для поиска по `full_name`.<br>
```python
{"match_phrase": {"full_name": {"query": "George Lucas"}}}
```
Нечеткий поиск по нескольким словам (нечеткий поиск - когда разрешено делать опечатки в словах).
Используется в `search_by_films` для поиска по `title` и `description`.<br>
В примере найдет все слова похожие на George и Lucas. (не фразовый поиск, а поиск отдельно по каждому слову)<br>
**Урок нечеткого поиска - [смотри урок](https://practicum.yandex.ru/trainer/middle-python/lesson/a062e471-010c-4d1c-8193-3835f1f7cbaa/)**.
```python
{"multi_match": {"query": George Lucas, "fuzziness": "auto","fields": ["title", "description"]}}
```

Фразовый поиск внутри `List[dict]`. Используется в `get_films` для поиска по полю `name` в `directors`,
`writers` и `actors`.<br>
```python
{"bool": {"must": [
    { "nested": { "path": "writers",
                "query": { "bool": { "must": [
                { "match_phrase": { "writers.name": {"query": "Geogre Lucas"}}}]}},}},]}}
```

### should, must, must not, filter в поисковых запросах
[Ссылка на урок](https://practicum.yandex.ru/trainer/middle-python/lesson/a062e471-010c-4d1c-8193-3835f1f7cbaa/)<br>
`must` — возвращённые данные обязательно должны соответствовать правилу, которое описано в этом ключе.<br>
`must_not` — возвращённые данные не должны соответствовать правилу, описанному в этом ключе.<br>
`filter` — похож на must, но с одним отличием. Найденные с помощью этих правил совпадения не будут участвовать в расчёте релевантности.<br>
`should` — возвращаемые данные обязательно должны соответствовать хотя бы одному правилу, которое описано в этом ключе. Он работает как ИЛИ для всех описанных внутри ключа правил.<br>

### Нюансы маппинга индекса
В примерах используется индекс `movies`.<br>
`writers` - List[dict]
```python
      "writers": {  // название ключа
        "type": "nested", // вложенный тип данных, здесь List[dict] - [{"id":"1", "name":"George Lucas"}]
        "dynamic": "strict", // динамическое создание полей запрещено, будут использованы только поля из properties.
        "properties": { // поля которые будут указаны
          "id": {  // ключ
            "type": "keyword" // тип keyword позволяет искать только точные совпадения текста.
          },
          "name": {
            "type": "text", // тип text наоборот позволяет вести поиск по подстрокам.
            "analyzer": "ru_en" // анализатор применяемый при поиске.
          }
        }
      }
```
`writers_names` - List[str]
```python
      "writers_names": {
        "type": "text",
        "analyzer": "ru_en"
      }
```
`genres` - List[str]
```python
      "genres": {"type":"text"} // поиск по всем словам, т.е подстроки в строке.
```
`id` - str (uuid)
```python
    "id": {"type": "keyword"} // поиск по одному слову, т.е либо найдет весь uuid, либо нет.
```
`imdb_rating` - float
```python
"imdb_rating": {"type": "float"}
```
`title` - str, содержит еще одно поле — title.raw. Оно нужно, чтобы у Elasticsearch была возможность делать сортировку, так как он не умеет сортировать данные по типу text.
```python
"title": {
    "type": "text",
    "analyzer": "ru_en",
    "fields": {
        "raw": {"type": "keyword"}
    }
}
```
### Запросы к Elasticsearch через curl
Посмотреть маппинг
```bash
curl -XGET http://172.18.0.5:9200/_mappings?pretty
```
Удалить индекс `movies`
```bash
curl -XDELETE http://172.18.0.5:9200/movies/
```
Получить документ по `id` из индекса `genre`
```bash
curl -XGET http://172.18.0.5:9200/genres/_doc/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff
```
Поиск по индексу `persons`
```bash
curl -XGET http://172.18.0.5:9200/persons/_search -H 'Content-Type: application/json' -d'
{
    "query": {
        "term": {
            "id": {
                "value": "26e83050-29ef-4163-a99d-b546cac208f8"
            }
        }
    }
}'
```
Мультипоиск по определенным полям + неточный поиск.
```bash
curl -XGET http://172.18.0.5:9200/movies/_search?pretty -H 'Content-Type: application/json' -d'
{
    "query": {
        "multi_match": {
            "query": "camp",
            "fuzziness": "auto",
            "fields": [
                "actors_names",
                "writers_names",
                "title",
                "description",
                "genres"
            ]
        }
    }
}'
```
`type:keyword` - регистрозависимый.<br>
`type:text`- регистронезависимый.<br>

## Ссылки
**Elasticsearch**<br>
[Поиск по List](https://www.elastic.co/guide/en/elasticsearch/guide/master/nested-query.html)<br>
[Снова вложенный запрос](https://opster.com/guides/elasticsearch/search-apis/elasticsearch-query-nested/)<br>
[Нечеткий поиск](https://www.geeksforgeeks.org/fuzzy-matching-in-elasticsearch/)<br>
[Настройки нечеткого поиска](https://opster.com/guides/elasticsearch/search-apis/elasticsearch-fuzzy-query/#Customizing-Fuzziness)<br>
[Операторы OR, AND, NOT - should, must, must not](https://opster.com/guides/elasticsearch/search-apis/elasticsearch-and-and-or-operators/#Using-the-OR-Operator-in-Elasticsearch)<br>
[Снова OR, AND, NOT](https://stackoverflow.com/questions/28538760/elasticsearch-bool-query-combine-must-with-or)<br>
[Описание match](https://www.mo4tech.com/elasticsearch-use-boolean-queries-to-improve-search-relevance.html)<br>
**Redis**<br>
[Учебник Redis](https://python-scripts.com/redis)<br>
[Теория кэширования](https://rutube.ru/video/86f8ec983f010f25af80f8af211f53f8/)

## На память
Получить название функции в которой выполняется код
```python
import inspect

def any_func():
    func_name = inspect.currentframe().f_code.co_name
    print(func_name)  # any_func
```

## Что можно улучшить
1) Возможно есть более удобные или универсальные поисковые запросы в эластик. (см. в `_build_query_request()`)
2) Улучшить способ маппинга эндпоинта, вызвавшего эластик с поисковым запросом. Сейчас при создании нового эндпоинта требуется его добавление в `_build_query_request()`. Изменение пути эндпоинта приведет к невозможности определить поисковый запрос. Возможное решение лежит в получении списка всех роутов...
3) Уменьшить зависимость от elasticsearch. Вынести elasticsearch в отдельный класс, аналогично кэшу.
   ```python
   @lru_cache()
    def get_film_service(
        cache: Cache = Depends(get_cache_storage),
        elastic: AsyncElasticsearch = Depends(get_elastic),
    ) -> BaseService:
        return FilmService(cache, elastic)
   ```
4) Использовать docker compose override для разделения dev-разработки на статичных ip и запуска прод-сервиса.
5) Поднять nginx  для api чтобы решить проблему 10к соединений
