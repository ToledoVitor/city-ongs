format:
	@poetry run ruff check --select I --fix . && ruff format .

pre-commit:
	@poetry run pre-commit install

shell:
	@poetry run python manage.py shell

makemigrations:
	@poetry run python manage.py makemigrations

migrate:
	@poetry run python manage.py migrate

collectstatic:
	@poetry run python manage.py collectstatic

superuser:
	@poetry run python manage.py shell -c "from accounts.models import User; \
	u, _ = User.objects.get_or_create(email='admin@admin.com'); \
	u.username = 'admin@admin.com'; \
	u.set_password('admin@2024'); \
	u.is_superuser = u.is_staff = True; \
	u.save(); \
	print('Superuser: admin@admin.com / admin@2024');"

run:
	@poetry run python manage.py runserver
