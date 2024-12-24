format:
	ruff format

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

collectstatic:
	python manage.py collectstatic

superuser:
	python manage.py createsuperuser

run:
	python manage.py runserver
