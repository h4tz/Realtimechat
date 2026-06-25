import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .connection_manager import manager
from .routers import chat, private
from .config import WS_HOST, WS_PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    await manager.connect()
    logger.info("WebSocket service started")
    yield
    await manager.disconnect()
    logger.info("WebSocket service stopped")


app = FastAPI(
    title="Chat WebSocket Service",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(private.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=WS_HOST, port=WS_PORT, reload=True)
