To run dev server:

```bash
docker compose -f docker-compose.dev.yml up
```

Autogenerate alembic migrations:

```bash
docker compose -f docker-compose.dev.yml run --rm app alembic revision --autogenerate -m "<your_message>"
```

To use alembic migrations:

```bash
docker compose -f docker-compose.dev.yml run --rm cockpit_api alembic upgrade head
```
