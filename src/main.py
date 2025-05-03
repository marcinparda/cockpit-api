from fastapi import FastAPI
from src.api.v1.endpoints import expenses, categories
from src.core.config import settings
from alembic.config import Config
from alembic import command
from src.core.config import settings
from contextlib import asynccontextmanager

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Run migrations at startup
#     alembic_cfg = Config("alembic.ini")
#     alembic_cfg.set_main_option(
#         "sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)
#     command.upgrade(alembic_cfg, "head")
#     yield
#     # Cleanup code can go here if needed


app = FastAPI(title="Cockpit API", version="0.0.1",
              docs_url="/api/docs")
# docs_url = "/api/docs", lifespan = lifespan)

app.include_router(
    expenses.router, prefix="/api/v1/expenses", tags=["expenses"])
app.include_router(categories.router,
                   prefix="/api/v1/categories", tags=["categories"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Cockpit API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
