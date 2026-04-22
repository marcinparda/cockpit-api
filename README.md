# Cockpit API

Cockpit API is the backend service for a personal productivity platform. Built with [FastAPI](https://fastapi.tiangolo.com/), it provides high performance, modern Python type safety, and automatic OpenAPI documentation.

### Services

- **Agent** — AI agent for CV tailoring; agentic loop with SSE streaming, LiteLLM (Claude), Serper web search, Redis CV read/write (`/api/v1/agent/`)
- **Budget** — expense tracking and budget management
- **Todos** — task and project management
- **Redis Store** — generic key-value store (`/api/v1/store/{prefix}/{category}/{key}`) backed by Redis, used by the CV app to store CV sections and preset registries
- **Authentication** — JWT-based sessions with cookie transport
- **Authorization** — role and permission management

### Agent service

Handles CV tailoring via an agentic LLM loop. All routes require authentication (`Features.AGENT` permission).

**Routes**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/agent/models` | List available LLM models |
| `GET` | `/api/v1/agent/conversations` | List user's conversations |
| `POST` | `/api/v1/agent/conversations` | Create conversation |
| `PATCH` | `/api/v1/agent/conversations/{id}` | Rename conversation |
| `DELETE` | `/api/v1/agent/conversations/{id}` | Delete conversation |
| `GET` | `/api/v1/agent/conversations/{id}/messages` | Get message history |
| `POST` | `/api/v1/agent/conversations/{id}/messages` | Send message → SSE stream |

**Agent tools (MVP)**

| Tool | Action |
|------|--------|
| `search_company` | POST to Serper API, returns top 5 organic results |
| `get_cv_base_preset` | Reads all 8 CV sections from `base:cv:*` in Redis |
| `create_cv_preset` | Proposes preset — emits `confirm_required` SSE, writes on next "yes" message |

**Environment variables required**

```bash
ANTHROPIC_API_KEY=   # from console.anthropic.com
SERPER_API_KEY=      # from serper.dev
```

**Module layout**

```
src/services/agent/
├── router.py          # FastAPI routes
├── schemas.py         # Pydantic request/response models
├── models.py          # SQLAlchemy: Conversation, Message
├── services.py        # Agentic loop + SSE generator
├── llm.py             # LiteLLM streaming wrapper + model list
├── tools.py           # Tool definitions (JSON schema for Claude)
├── tools_executor.py  # Executes tool calls, returns results
└── repository.py      # DB access for conversations/messages
```

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
