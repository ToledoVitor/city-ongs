# Multi-stage so the compiler toolchain never reaches the published image.
# psycopg2 (2.9.12) ships sdist-only, so it compiles from source and needs
# gcc + libpq-dev at build time — but only libpq5 at runtime.

FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN uv sync --frozen --no-dev


FROM python:3.12-slim

# pt_BR.UTF-8 is load-bearing: contracts/views.py calls
# locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8") and raises locale.Error
# if the locale was never generated.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 locales && \
    echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8

# Mount point for the django_settings secret
RUN mkdir -p /secrets

WORKDIR /app

ENV PATH=/opt/venv/bin:$PATH

COPY --from=builder /opt/venv /opt/venv

COPY . /app/

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "core.wsgi"]
