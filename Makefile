up:
	docker compose up

build:
	docker compose up --build

build-d:
	docker compose up --build -d

down:
	docker compose down

down-v:
	docker compose down -v

shell:
	docker compose exec web bash

make-usecase:
	docker compose exec web python manage.py make_usecase

migrate:
	docker compose exec web python manage.py makemigrations
	docker compose exec web python manage.py migrate

superuser:
	docker compose exec web python manage.py createsuperuser

logs:
	docker compose logs -f web

frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

frontend-check:
	cd frontend && npm run check

fullstack:
	docker compose -f docker-compose.yml -f docker-compose.frontend.yml up --build

.PHONY: runtime-check parity-check restore-drill
runtime-check:
	bash tools/django-runtime/validate.sh

parity-check:
	CONTRACT_PRODUCTION=1 bash tools/http-contracts/compare.sh

restore-drill:
	bash tools/django-runtime/restore-drill.sh
