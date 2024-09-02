# Read-Only API для доступа к фильмам, жанрам и персонам.

### Заметки
Все чтение идет из elasticsearch.
Поэтому нет полей created, modified.

Данные в elasticsearch попадают через ETL с 3го спринта (new_admin_panel_sprint_3)

models.Film нужен для валидации данных из elasticsearch.
api.v1.film.Film - DTO, трансформирует данные из models.Film в данные, которые должен увидеть пользователь через API.
