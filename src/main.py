from fastapi import FastAPI, Depends
from src.api.v1.endpoints import expenses, categories, payment_methods, api_key
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-KEY")

app = FastAPI(title="Cockpit API", version="0.0.1",
              docs_url="/api/docs", dependencies=[Depends(api_key_header)])

app.include_router(
    expenses.router, prefix="/api/v1/expenses", tags=["expenses"])
app.include_router(categories.router,
                   prefix="/api/v1/categories", tags=["categories"])
app.include_router(
    payment_methods.router, prefix="/api/v1/payment_methods", tags=["payment_methods"])
app.include_router(
    api_key.router, prefix="/api/v1/api_key", tags=["api_key"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Cockpit API!"}

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
