# Rules

## General Guidelines

- Project uses poetry for dependency management
- Ensure to run `poetry install` after modifying `pyproject.toml`
- All new files should be added to the appropriate directories
- Database and API is hosted via Docker, API container name is `cockpit-api` so fe. to upgrade the database run `docker compose -f docker-compose.dev.yml run --rm cockpit_api alembic upgrade head`
- Postgres dev envs are: DB_USER=cockpit_user, DB_PASSWORD=secure_dev_password, DB_HOST=cockpit_db_host, DB_NAME=cockpit_db
- you can run tests with `poetry run pytest` instead of `docker compose -f docker-compose.dev.yml run --rm cockpit_api pytest`
- If they are warnings in tests, address them before committing, you can do it as a last step before creating summary
- There is no need to restart docker API container after changes, it configured to refresh automatically on code changes.

## Python

- Use Python type hints for all function signatures.
- Remove unused imports, especially from `src.core.database` and `src.core.config`.
- When creating a models remember to use `BaseModel` from `src.models.base`/`.base`.
- Do not put anything in `__init_.py` files, even documentation, if there is no obligatory need to do so
- When importing modules, use absolute imports from the `src` directory to maintain consistency and clarity.
- When importing a modules try to use imports at the top of the file, not in the middle of the code or functions unless absolutely necessary.

## FastAPI

- Organize endpoints using `APIRouter`.
- Validate request/response models with Pydantic.
- Write async endpoints where appropriate.
- Use pytest for testing API endpoints.
- Endpoints should have not trailing slashes in their paths.

## Documentation

- instead of adding response and requests schema documentation in the endpoint via docstrings, use Pydantic models and FastAPI's `response_model` and `request_body` parameters in the endpoint decorators, but you can still use docstrings for additional information like descriptions
- Use docstrings for endpoint descriptions and parameter explanations.
