# Image built by CodeBuild and run on Fargate.
#
# This file is the image the pipeline actually builds. It is not one of the
# Dockerfiles already in the assettracker repository:
#
#   docker/production/django/Dockerfile
#     still expects PostgreSQL, starts gunicorn as jobportal.wsgi, and
#     listens on port 1998. That does not match this project.
#
#   docker/local/django/Dockerfile
#     matches MySQL and port 8000, then runs Django's development server
#     and also installs Streamlit. The entrypoint imports mysql.connector
#     and blocks startup on MYSQL_* variables.
#
# This image follows the working local stack (MySQL, port 8000, development
# settings) and starts gunicorn, which is the process you want behind a
# load balancer.

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=asset_tracker.settings.development

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/requirements
COPY requirements/production.txt requirements/common.txt ./
RUN pip install --no-cache-dir -r production.txt "gunicorn==22.0.0"

WORKDIR /app
COPY . /app
RUN mkdir -p /app/logs /app/static /app/media \
    && touch /app/.env \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# migrate runs on startup because this practice service has one task.
# Scale past one task only after migrations move to their own step.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn asset_tracker.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
