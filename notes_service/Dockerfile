FROM python:3.12-slim AS builder

ARG PROJECT_ROOT=$HOME/app/

WORKDIR $PROJECT_ROOT
COPY ./pyproject.toml pyproject.toml

RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc \
    && pip install --no-cache-dir uv && uv sync 

FROM python:3.12-slim

ARG PROJECT_ROOT=$HOME/app/

WORKDIR $PROJECT_ROOT

COPY . .
COPY --from=builder $PROJECT_ROOT/.venv $PROJECT_ROOT/.venv

ENV PATH="$PROJECT_ROOT/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get upgrade -y \
    && rm -rf /var/cache/apt/archives/* && rm -rf /var/lib/apt/lists/* \
    && chmod +x ./entrypoint.sh

CMD ["./entrypoint.sh"]