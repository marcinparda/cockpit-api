# Custom instructions for Copilot

## FastAPI

- Use Python type hints for all function signatures.
- Organize endpoints using APIRouter.
- Validate request/response models with Pydantic.
- Write async endpoints where appropriate.
- Use pytest for testing API endpoints.
- remove unused imports, especially from `src.core.database` and `src.core.config`

## Documentation

- Add OpenAPI documentation via FastAPI's built-in features. Use `response_model` for responses and schemas for request bodies.
- Use docstrings for endpoint descriptions and parameter explanations.
