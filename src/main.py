from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.endpoints import expenses, categories, payment_methods, todo_items, todo_projects, shared
from src.core.config import settings
from typing import List

app = FastAPI(title="Cockpit API", version="0.0.1",
              docs_url="/api/docs")

origins: List[str] = [str(origin) for origin in settings.CORS_ORIGINS] if isinstance(
    settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(
    expenses.router, prefix="/api/v1/expenses", tags=["ai-budget/expenses"])
app.include_router(categories.router,
                   prefix="/api/v1/categories", tags=["ai-budget/categories"])
app.include_router(
    payment_methods.router, prefix="/api/v1/payment_methods", tags=["ai-budget/payment_methods"])
app.include_router(
    todo_items.router, prefix="/api/v1/todo/items", tags=["todo/todo_items"])
app.include_router(
    todo_projects.router, prefix="/api/v1/todo/projects", tags=["todo/todo_projects"])
app.include_router(
    shared.router, prefix="/api/v1/shared", tags=["shared"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Cockpit API!"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
