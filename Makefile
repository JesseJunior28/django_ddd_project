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