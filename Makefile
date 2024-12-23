format:
	ruff format

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

run:
	python manage.py runserver
