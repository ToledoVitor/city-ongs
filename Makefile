.DEFAULT_GOAL := help

.PHONY: help format pre-commit shell makemigrations migrate seed collectstatic \
        superuser run test test-sqlite check audit-templates ui-mockup \
        up up-daemon down

help:  ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-18s\033[0m %s\n", $$1, $$2}'

format:  ## Sort imports and format with ruff
	@uv run ruff check --select I --fix . && uv run ruff format .

pre-commit:  ## Install the pre-commit hook
	@uv run pre-commit install

shell:  ## Django shell with utils.shell preloaded
	@uv run python manage.py shell -c "import utils.shell"

check:  ## Django system checks + verify no migrations are missing (no DB needed)
	@uv run python manage.py check
	@uv run python manage.py makemigrations --check --dry-run

makemigrations:  ## Create migrations for model changes
	@uv run python manage.py makemigrations

migrate:  ## Apply migrations
	@uv run python manage.py migrate

seed:  ## Seed development data (idempotent)
	@uv run python manage.py seed_dev

collectstatic:  ## Collect static files
	@uv run python manage.py collectstatic

test:  ## Run the test suite (needs Postgres — see `make up`)
	@uv run python manage.py test

test-sqlite:  ## Run the test suite against sqlite :memory: (no Postgres needed)
	@uv run python manage.py test --settings=core.settings_sqlite_test

audit-templates:  ## Report which templates are on the design system
	@uv run python tools/audit_templates.py

ui-mockup:  ## Regenerate the UI primitives gallery from the shipped CSS
	@uv run python tools/build_ui_mockup.py

superuser:  ## Create/reset the local admin user
	@uv run python manage.py shell -c "from accounts.models import User; \
	u, _ = User.objects.get_or_create(email='vitor@admin.com'); \
	u.username = 'vitoradmin@admin.com'; \
	u.set_password('admin@2024'); \
	u.is_superuser = u.is_staff = True; \
	u.save(); \
	print('Superuser: vitor@admin.com / admin@2024');"

run:  ## Run the dev server
	@uv run python manage.py runserver

up:  ## Start Postgres + app in Docker
	@docker compose up --build

up-daemon:  ## Start Postgres + app in Docker, detached
	@docker compose up -d --build

down:  ## Stop the Docker stack
	@docker compose down
