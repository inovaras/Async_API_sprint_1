FROM python:3.11-slim

WORKDIR /async_api/src
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY configs /configs
COPY ./async_api/src .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
