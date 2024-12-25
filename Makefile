format:
	ruff format

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

collectstatic:
	python manage.py collectstatic

superuser:
	@poetry run python manage.py shell -c "from accounts.models import User; \
	u, _ = User.objects.get_or_create(email='admin@admin.com'); \
	u.username = 'admin@admin.com'; \
	u.set_password('admin@2024'); \
	u.is_superuser = u.is_staff = True; \
	u.save(); \
	print('Superuser: admin@admin.com / admin@2024');"

run:
	python manage.py runserver
