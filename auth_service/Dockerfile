FROM python:3.12-slim

WORKDIR app/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get upgrade -y && rm -rf /var/cache/apt/archives/*

COPY . .

RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -r requirements.txt \
    && chmod +x ./entrypoint.sh

CMD ["./entrypoint.sh"]