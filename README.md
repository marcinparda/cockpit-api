# Cockpit API

Cockpit API is the backend service for a personal productivity platform. Built with [FastAPI](https://fastapi.tiangolo.com/), it provides high performance, modern Python type safety, and automatic OpenAPI documentation.

### Services

- **Budget** — expense tracking and budget management
- **Todos** — task and project management
- **Redis Store** — generic key-value store (`/api/v1/store/{prefix}/{category}/{key}`) backed by Redis, used by the CV app to store CV sections and preset registries
- **Authentication** — JWT-based sessions with cookie transport
- **Authorization** — role and permission management

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation & Running the API

Prepare your environment by copying the example environment file:

```bash
cp .env.example .env
```

Update the `.env` file with your database connection details and other configurations.

Start the development server using Docker Compose:

```bash
docker compose -f docker-compose.dev.yml up
```

### Database Migrations

Autogenerate alembic migrations:

```bash
docker compose -f docker-compose.dev.yml run --rm app alembic revision --autogenerate -m "<your_message>"
```

To use alembic migrations:

```bash
docker compose -f docker-compose.dev.yml run --rm cockpit_api alembic upgrade head
```

The API will be available at [http://localhost:8000](http://localhost:8000).

### API Documentation

- Swagger UI: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

## Contributing

Contributions are not welcome yet! This project is currently in its early stages, and I am focusing on building the core features. However, if you have suggestions or ideas, feel free to open an issue.

## License

This project is licensed under the MIT License.

```
