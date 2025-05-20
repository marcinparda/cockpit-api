from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.endpoints import expenses, categories, payment_methods, shopping_items
from src.auth.dependencies import api_key_header
from src.core.config import settings

app = FastAPI(title="Cockpit API", version="0.0.1",
              docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(
    expenses.router, prefix="/api/v1/expenses", tags=["expenses"])
app.include_router(categories.router,
                   prefix="/api/v1/categories", tags=["categories"])
app.include_router(
    payment_methods.router, prefix="/api/v1/payment_methods", tags=["payment_methods"])
app.include_router(
    shopping_items.router, prefix="/api/v1/shopping", tags=["shopping"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Cockpit API!"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
