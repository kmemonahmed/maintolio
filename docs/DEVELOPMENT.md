# Development

This guide covers the common local development workflow for Maintolio.

## Requirements

- Docker
- Docker Compose
- Make, optional but convenient

## Environment Setup

Create a local `.env` file:

```bash
cp .env.example .env
```

Do not commit real secrets in `.env`.

## Docker Commands

Start the full stack:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
```

Stop containers:

```bash
docker compose down
```

Stop containers and remove local Docker volumes:

```bash
docker compose down -v
```

The `-v` form deletes local database and RabbitMQ data. Use it only when you want a fresh local environment.

## Makefile Shortcuts

```bash
make build
make up
make down
make logs
make migrate
make makemigrations
make createsuperuser
make shell
make test
make seed
make celery-logs
```

## Migrations

Create migrations:

```bash
docker compose exec web python manage.py makemigrations
```

Apply migrations:

```bash
docker compose exec web python manage.py migrate
```

## Demo Seed Data

Run:

```bash
docker compose exec web python manage.py seed_demo_data
```

Demo users:

```text
owner@techcare.test / Test@12345
admin@techcare.test / Test@12345
manager@techcare.test / Test@12345
technician1@techcare.test / Test@12345
technician2@techcare.test / Test@12345
rahim@abchospital.test / Test@12345
```

## Tests

Run the test suite inside Docker:

```bash
docker compose exec web python manage.py test
```

The Docker command is preferred because `.env` uses Docker service hostnames such as `DB_HOST=db`.

## Django Shell

```bash
docker compose exec web python manage.py shell
```

## Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

## Celery

The local stack runs:

- `rabbitmq`: Celery broker
- `redis`: result backend and cache backend
- `celery_worker`: executes tasks
- `celery_beat`: schedules periodic tasks

View Celery logs:

```bash
docker compose logs -f celery_worker celery_beat
```

## RabbitMQ Dashboard

RabbitMQ management UI:

```text
http://127.0.0.1:15672
```

Default local credentials:

```text
guest / guest
```

## Swagger Docs

```text
http://127.0.0.1:8000/api/docs/
```

## Common Troubleshooting

### Port 5432 Already in Use

The Docker Postgres service is exposed as `5433:5432`, so it should not conflict with a local Postgres running on `5432`.

Connect from the host with port `5433`. Inside Docker, use `DB_HOST=db` and `DB_PORT=5432`.

### Migration Needed

If endpoints fail because tables are missing, run:

```bash
docker compose exec web python manage.py migrate
```

### Existing Docker Volume Has Old Database Credentials

If you changed DB credentials after a volume was already created, Postgres may keep the old user/password. For this local dev setup, either repair ownership:

```bash
make fix-db-owner
```

Or reset the local database completely:

```bash
make reset-db
make migrate
make seed
```

`make reset-db` removes Docker volumes and deletes local container database data.

### Celery Worker Not Receiving Tasks

Check that RabbitMQ is healthy:

```bash
docker compose ps
docker compose logs -f rabbitmq
```

Then check worker logs:

```bash
docker compose logs -f celery_worker
```

### Redis or RabbitMQ Connection Issue

Restart services:

```bash
docker compose restart redis rabbitmq celery_worker celery_beat
```

Confirm `.env` contains:

```text
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_CACHE_URL=redis://redis:6379/1
```
