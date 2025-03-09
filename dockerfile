FROM python:3.12

RUN apt-get update && \
    apt-get install -y locales && \
    echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen pt_BR.UTF-8

ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8

RUN mkdir -p /secrets

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.in-project false && poetry install --no-root

COPY . /app/

EXPOSE 8080

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "core.wsgi"]
