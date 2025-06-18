from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from core.database import db_control

from core.config import settings

from api import router as api_router

from pathlib import Path # Более современный способ работы с путями


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    yield
    # shutdown
    await db_control.dispose()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None if settings.run.mode == "production" else "/docs", #disables docs
    redoc_url=None if settings.run.mode == "production" else "/redoc", #disables redoc
    openapi_url=None if settings.run.mode == "production" else "/openapi.json", #disables openapi.json suggested by tobias comment.
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.httpcors.urls, #pyright:ignore
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )

