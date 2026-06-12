COMPOSE = docker compose

.PHONY: build up down logs migrate makemigrations createsuperuser shell test seed celery-logs fix-db-owner reset-db

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f web

migrate:
	$(COMPOSE) exec web python manage.py migrate

makemigrations:
	$(COMPOSE) exec web python manage.py makemigrations

createsuperuser:
	$(COMPOSE) exec web python manage.py createsuperuser

shell:
	$(COMPOSE) exec web python manage.py shell

test:
	$(COMPOSE) exec web python manage.py test

seed:
	$(COMPOSE) exec web python manage.py seed_demo_data

celery-logs:
	$(COMPOSE) logs -f celery_worker celery_beat

fix-db-owner:
	$(COMPOSE) exec -T -e PGPASSWORD=admin db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "DO \$$$$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'maintolio') THEN CREATE ROLE maintolio LOGIN PASSWORD 'maintolio' CREATEDB; ELSE ALTER ROLE maintolio WITH LOGIN PASSWORD 'maintolio' CREATEDB; END IF; END \$$$$;"
	$(COMPOSE) exec -T -e PGPASSWORD=admin db sh -c "if ! psql -U postgres -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='maintolio'\" | grep -q 1; then createdb -U postgres -O maintolio maintolio; fi"
	$(COMPOSE) exec -T -e PGPASSWORD=admin db psql -U postgres -d maintolio -v ON_ERROR_STOP=1 -c "DO \$$$$ DECLARE item record; BEGIN FOR item IN SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public' LOOP EXECUTE format('ALTER TABLE %I.%I OWNER TO maintolio', item.schemaname, item.tablename); END LOOP; FOR item IN SELECT sequence_schema, sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public' LOOP EXECUTE format('ALTER SEQUENCE %I.%I OWNER TO maintolio', item.sequence_schema, item.sequence_name); END LOOP; FOR item IN SELECT table_schema, table_name FROM information_schema.views WHERE table_schema = 'public' LOOP EXECUTE format('ALTER VIEW %I.%I OWNER TO maintolio', item.table_schema, item.table_name); END LOOP; END \$$$$;" -c "ALTER SCHEMA public OWNER TO maintolio;" -c "GRANT ALL ON SCHEMA public TO maintolio;" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO maintolio;" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO maintolio;"

reset-db:
	$(COMPOSE) down -v
	$(COMPOSE) up --build -d
