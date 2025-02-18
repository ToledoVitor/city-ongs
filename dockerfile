FROM python:3.12

RUN mkdir -p /secrets

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.in-project false && poetry install --no-root

COPY . /app/

EXPOSE 8000

CMD ["sh", "-c", "poetry run gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers=2 --threads=4 --timeout 0"]
