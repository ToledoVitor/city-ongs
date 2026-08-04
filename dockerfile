# Multi-stage so the compiler toolchain never reaches the published image.
# psycopg2 (2.9.12) ships sdist-only, so it compiles from source and needs
# gcc + libpq-dev at build time — but only libpq5 at runtime.
#
# Worth restating, because dropping psycopg2-binary makes collapsing this into
# a single stage look tempting: the binary wheel would remove the need for a
# builder, but it bundles its own libssl/libcrypto, and this image already
# loads `cryptography` (via google-cloud-*) in the same process. That is the
# exact conflict psycopg upstream warns about, and it buys nothing — the
# builder stage costs build time, not image size.

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

# Unbuffered so Cloud Logging sees a crash traceback before the instance dies.
ENV PYTHONUNBUFFERED=1

# Mount point for the django_settings secret
RUN mkdir -p /secrets

WORKDIR /app

ENV PATH=/opt/venv/bin:$PATH

COPY --from=builder /opt/venv /opt/venv

COPY . /app/

EXPOSE 8080

# One worker, several threads. Memory is what Cloud Run bills per instance-
# second, and a second worker would duplicate the whole ~150 MiB interpreter
# for no extra throughput at this traffic level; threads share it. Four is
# also the per-instance connection ceiling, since Django keeps one Postgres
# connection per thread (see CONN_MAX_AGE in core/settings.py) — with
# max-instances=2 that is at most 8 connections against the database.
#
# --timeout 0 disables gunicorn's own clock on purpose: Cloud Run already
# bounds request duration, and a PDF export can legitimately run long.
#
# --max-requests recycles the worker periodically. Report rendering leaves
# behind memory the allocator does not return to the OS, so a long-lived
# worker's RSS drifts upward; recycling puts a hard floor under that instead
# of letting it creep toward the instance limit.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "0", \
     "--max-requests", "400", \
     "--max-requests-jitter", "50", \
     "core.wsgi"]
