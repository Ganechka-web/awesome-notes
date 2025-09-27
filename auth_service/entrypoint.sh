#!/bin/sh

# run migrations
alembic upgrade head

# application startup
python3 -m src.main
