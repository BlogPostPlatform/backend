# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.14.6-slim
ARG UV_VERSION=0.11.32

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM ${PYTHON_IMAGE} AS builder

ARG INSTALL_DEV_DEPENDENCIES=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

# Install from the lockfile before copying source so this layer is reusable.
# Compose explicitly opts development images into the additional groups.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    if [ "${INSTALL_DEV_DEPENDENCIES}" = "true" ]; then \
      uv sync --locked --all-groups --no-install-project; \
    else \
      uv sync --locked --no-dev --no-install-project; \
    fi

FROM ${PYTHON_IMAGE} AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    TZ=Asia/Tashkent

WORKDIR /app

# Tini remains PID 1 in Docker Compose and Kubernetes, forwarding signals and
# reaping orphaned child processes for every application role.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*

# Production uses stable high IDs; development can match the host user.
RUN groupadd --gid "${APP_GID}" app && \
    useradd --uid "${APP_UID}" --gid app --home-dir /nonexistent \
      --shell /usr/sbin/nologin --no-create-home app

# Dependencies and source remain root-owned and cannot be modified at runtime.
COPY --from=builder /opt/venv /opt/venv
COPY . .
RUN sed -i 's/\r$//' /app/entrypoints/*.sh && \
    chmod 0755 /app/entrypoints/*.sh && \
    mkdir -p /app/media && \
    DJANGO_SETTINGS_MODULE=core.settings.base USE_S3=false \
      python manage.py collectstatic --noinput && \
    chown -R app:app /app/media

USER app

EXPOSE 8000
STOPSIGNAL SIGTERM

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/entrypoints/django.sh"]
