FROM python:3.11-slim

WORKDIR /async_api

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY configs .
COPY ./async_api .


CMD ["bash", "-c", "fastapi dev src/main.py"]