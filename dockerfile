FROM python:3.12

RUN mkdir -p /secrets

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.in-project false && poetry install --no-root

COPY . /app/

EXPOSE 8080

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "core.wsgi"]
