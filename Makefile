format:
	@uv run ruff check --select I --fix . && uv run ruff format .

pre-commit:
	@uv run pre-commit install

shell:
	@uv run python manage.py shell -c "import utils.shell"

makemigrations:
	@uv run python manage.py makemigrations

migrate:
	@uv run python manage.py migrate

seed:
	@uv run python manage.py seed_dev

collectstatic:
	@uv run python manage.py collectstatic

superuser:
	@uv run python manage.py shell -c "from accounts.models import User; \
	u, _ = User.objects.get_or_create(email='vitor@admin.com'); \
	u.username = 'vitoradmin@admin.com'; \
	u.set_password('admin@2024'); \
	u.is_superuser = u.is_staff = True; \
	u.save(); \
	print('Superuser: admin@admin.com / admin@2024');"

run:
	@uv run python manage.py runserver

up:
	@docker compose up --build

up-daemon:
	@docker compose up -d --build

down:
	@docker compose down
