from fastapi import FastAPI
from contextlib import asynccontextmanager
from .core.database import init_db

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    init_db()
    yield
    # Shutdown code (if any)

app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok"}
