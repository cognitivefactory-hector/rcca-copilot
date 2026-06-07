FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first for layer caching. pyproject defines them.
COPY pyproject.toml README.md LICENSE ./
RUN pip install --upgrade pip && pip install ".[dev]"

COPY . .

EXPOSE 8000

# entrypoint applies migrations then serves; overridable in compose.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
