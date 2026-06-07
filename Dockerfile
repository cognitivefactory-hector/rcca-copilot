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

# entrypoint: migrate, collect static (whitenoise serves them), then serve.
# Overridden in docker-compose for local dev (runserver). $PORT is set by Render.
# --timeout 120: a synchronous agent run (tool loop + structured emit) exceeds
#   gunicorn's default 30s worker timeout, which would kill the worker mid-request.
# --threads 8: the agent call is mostly I/O wait on the Anthropic API (GIL
#   released), so threads keep the app responsive during a run on a single,
#   memory-light worker (Render free tier).
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 8 --timeout 120"]
