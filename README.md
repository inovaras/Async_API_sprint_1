# Проектная работа 4 спринта

**Важное сообщение для тимлида:** для ускорения проверки проекта укажите ссылку на приватный репозиторий с командной работой в файле readme и отправьте свежее приглашение на аккаунт [BlueDeep](https://github.com/BigDeepBlue).

В папке **tasks** ваша команда найдёт задачи, которые необходимо выполнить в первом спринте второго модуля.  Обратите внимание на задачи **00_create_repo** и **01_create_basis**. Они расцениваются как блокирующие для командной работы, поэтому их необходимо выполнить как можно раньше.

Мы оценили задачи в стори поинтах, значения которых брались из [последовательности Фибоначчи](https://ru.wikipedia.org/wiki/Числа_Фибоначчи) (1,2,3,5,8,…).

Вы можете разбить имеющиеся задачи на более маленькие, например, распределять между участниками команды не большие куски задания, а маленькие подзадачи. В таком случае не забудьте зафиксировать изменения в issues в репозитории.

**От каждого разработчика ожидается выполнение минимум 40% от общего числа стори поинтов в спринте.**


# Асинхронный API с кэшированием и поиском в Elasticsearch
Кэширование находится в ```services.film.py```.<br>
Запросы к elasticsearch в ```services.film.py``` и ```api.v1.*.py```.

## Требования перед установкой
1) Linux (проект разработан на Ubuntu 22.04.4 LTS)
2) python >= 3.10
3) Docker

Скачать репозиторий и перейти в него.
```bash
git clone git@github.com:NankuF/Async_API_sprint_1.git && cd ./Async_API_sprint_1
```
Установить виртуальное окружение и зависимости.
```bash
python3 -m venv venv && . ./venv/bin/activate && pip install -r requirements.txt
```

## Установка
Проект разворачивается через docker compose.<br>
Используется сеть со статичными адресами для устранения проблемы смены ip адресов при перезапуске контейнеров.<br>
Используются созданные вручную контейнеры для предотвращения потери данных.<br>

В проекте используется код из ранее выполненных спринтов, спринты загружены в виде образов на docker hub.
[Админка](https://github.com/NankuF/new_admin_panel_sprint_2)
```yaml
  service:
    image: inovaras/admin-app
```
[ETL процесс](https://github.com/NankuF/new_admin_panel_sprint_3) обновления данных из postgresql в elasticsearch при внесении изменений через админку.
```yaml
  admin-etl-process:
    image: inovaras/admin-etl
```
Перед установкой необходимо перейти в директорию с репозиторием и выполнить скрипт, разворачивающий сеть и volumes.
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
Переименовать `.env.example` в `.env`
```bash
mv .env.example .env
```
Запустить docker compose (docker-compose.yml должен находиться в этой же директории)
```bash
docker compose up -d --build
```
Убедиться что etl-процессы отработали успешно. Перенесены фильмы, персоны и жанры в elasticsearch.
```bash
curl -XGET http://172.18.0.5:9200/_cat/indices?v
```
В колонке docs.count указано кол-во документов пересенных ETL-процессом.
```text
health status index   uuid                   pri rep docs.count docs.deleted store.size pri.store.size
yellow open   movies  FJsV8_apRj6sOfOMCVJ_XQ   1   1       6782            0      1.5mb          1.5mb
yellow open   persons SwhRqmCmSTOmhfD2uwAEyA   1   1       4166            0        1mb            1mb
yellow open   genres  bbZVj-KTSs6SLV1Nfl3OOg   1   1         26            0      9.7kb          9.7kb

```
Запустить приложение
```bash
fastapi dev main.py
```
Открыть приложение перейдя по адресу
```text
http://127.0.0.1:8000/api/openapi#/
```

## Ожидаемое поведение
- API собрано по [ТЗ](https://practicum.yandex.ru/learn/middle-python/courses/7c4e333e-2395-4f53-88af-256bc6aab346/sprints/231500/topics/7ee9e96e-c2e8-4a7b-9b5c-b626a91aa234/lessons/3d52a604-2fcd-4593-8f4b-065e8cb6af75/)
- Все эндпоинты кешируются по uuid, либо по составному ключу.
   - По uuid кэшируются запросы для одного объекта(персона, фильм, жанр)
   - По составному ключу кэшируются запросы для получения списка объектов.<br>
   - Поиск сначала производится в кэше, затем в elasticsearch. Ответ возвращается в API.<br>
Шаблон составного ключа cмотри в разделе Redis.<br>
**Важно! Параметры сортировки, пагинации и поиска(фильтрации) должны быть указаны в составном ключе, иначе запрос кешируется и данные отображаются неверно.**<br>
## Redis
Кэширование проверяется до запроса в elasticsearch.<br>
Кэш записывается после запроса в elasticsearch.<br>
Срок жизни кэша указан в `.env`:<br>
`FILM_CACHE_EXPIRE_IN_SECONDS=300`<br>
`PERSON_CACHE_EXPIRE_IN_SECONDS=300`<br>
`GENRE_CACHE_EXPIRE_IN_SECONDS=300`<br>

Кэширование одиночного объекта:<br>
`_get_object_from_cache`<br>
`_put_object_to_cache`<br>

Кэширование списка объектов:<br>
`_get_objects_from_cache`<br>
`_put_objects_to_cache`<br>

Обертки для кэширования в redis и поиска в elasticsearch:<br>
`get_film_by_id`<br>
`get_person_by_id`<br>
`get_genre_by_id`<br>
`get_genre_by_name`<br>
`get_objects`<br>

Шаблон составного ключа:<br>
```
<название функции>_<параметры пагинации>_<параметры сортировки>_<поисковый запрос>
```
`<название функции>` - название функции, из которой был отправлен запрос.<br>
`<параметры пагинации>`- номер страницы и кол-во объектов на страницу. (page, per_page).<br>
`<параметры сортировки>` - запрос, по которому была применена сортировка. Пример: "-imdb_rating".<br>
`<поисковый запрос>`- запрос, по которому собраны данные. Пример: "George Lucas".<br>
**Важно! Параметры сортировки, пагинации и поиска(фильтрации) должны быть указаны в составном ключе, иначе запрос кешируется и данные отображаются неверно.**<br>

## Elasticsearch
Данные собираются из elasticsearch при помощи поисковых запросов.<br>
Примеры:<br>
Запрос для поиска id в любом из трех `List[str]`. Используется в `person_films` для поиска роли по `uuid` в `directors`
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
**Возможно запрос нечеткого поиска можно упростить - [смотри урок](https://practicum.yandex.ru/trainer/middle-python/lesson/a062e471-010c-4d1c-8193-3835f1f7cbaa/)**
```python
filters = []
words = "Geoge Lucs".split(" ")
for word in words:
    filters.append(
        {"fuzzy": {"title": {"value": word, "fuzziness": "AUTO"}}},
    )
filter_query = {"bool": {"should": filters}}
```
Упростить вот так (требует проверки)
```python
{"match": {
    "text_field": {
                "query": "whit code",
                "fuzziness": "auto"
            }}}
```

Фразовый поиск внутри `List[str]`. Используется в `get_films` для поиска по полю `name` в `directors`
`writers` и `actors`.<br>
```python
{"bool": {"must": [
    { "nested": { "path": "writers",
                "query": { "bool": { "must": [
                { "match_phrase": { "writers.name": {"query": "Geogre Lucas"}}}]}},}},]}}
```

### should, must, must not, filter в поисковых запросах
[Ссылка на урок](https://practicum.yandex.ru/trainer/middle-python/lesson/a062e471-010c-4d1c-8193-3835f1f7cbaa/)
`must` — возвращённые данные обязательно должны соответствовать правилу, которое описано в этом ключе.
`must_not` — возвращённые данные не должны соответствовать правилу, описанному в этом ключе.
`filter` — похож на must, но с одним отличием. Найденные с помощью этих правил совпадения не будут участвовать в расчёте релевантности.
`should` — возвращаемые данные обязательно должны соответствовать хотя бы одному правилу, которое описано в этом ключе. Он работает как ИЛИ для всех описанных внутри ключа правил.

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
      },
```
`genres` - List[str]
```python
      "genres": {"type":"text"} // поиск по всем словам, т.е подстроки в строке.
```
id - str (uuid)
```python
    "id": {"type": "keyword"}, // поиск по одному слову, т.е либо найдет весь uuid, либо нет.
```
imdb_rating - float
```python
"imdb_rating": {"type": "float"},
```

### Запросы к Elasticsearch через curl
Получить 1 документ - genre
```bash
curl -XGET http://172.18.0.5:9200/genres/_doc/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff
```


### Ссылки
**Elasticsearch**<br>
[Поиск по List](https://www.elastic.co/guide/en/elasticsearch/guide/master/nested-query.html)<br>
[Снова вложенный запрос](https://opster.com/guides/elasticsearch/search-apis/elasticsearch-query-nested/)
[Нечеткий поиск](https://www.geeksforgeeks.org/fuzzy-matching-in-elasticsearch/)<br>
[Настройки нечеткого поиска](https://opster.com/guides/elasticsearch/search-apis/elasticsearch-fuzzy-query/#Customizing-Fuzziness)<br>
[Операторы OR, AND, NOT - should, must, must not](https://opster.com/guides/elasticsearch/search-apis/elasticsearch-and-and-or-operators/#Using-the-OR-Operator-in-Elasticsearch)<br>
[Снова OR, AND, NOT](https://stackoverflow.com/questions/28538760/elasticsearch-bool-query-combine-must-with-or)<br>
[match](https://www.mo4tech.com/elasticsearch-use-boolean-queries-to-improve-search-relevance.html)<br>
**Redis**<br>
[Учебник Redis](https://python-scripts.com/redis)<br>