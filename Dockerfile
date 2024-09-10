FROM python:3.11-slim

WORKDIR /async_api/src

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn uvicorn-worker

COPY configs /configs
COPY ./async_api/src .

EXPOSE 8080

# Gunicorn -  это менеджер процессов, который будет управлять FastAPI-приложением.
# Uvicorn: хотя используется Gunicorn, FastAPI сервер по-прежнему работает через Uvicorn, поэтому эта зависимость обязательна.
# Запуск Gunicorn с UvicornWorker для продакшен-окружения:
CMD ["gunicorn", "-w", "4", "-k", "uvicorn_worker.UvicornH11Worker", "--bind", "0.0.0.0:8080", "main:app"]

# для дебага:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
