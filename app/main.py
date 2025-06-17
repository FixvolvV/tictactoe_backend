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

    current_dir = Path(__file__).parent

    # Полные пути к файлам сертификатов
    ssl_keyfile_path = current_dir / "localhost+2-key.pem"
    ssl_certfile_path = current_dir / "localhost+2.pem"

    # Проверка существования файлов (опционально, но хорошая практика)
    if not ssl_keyfile_path.exists():
        print(f"Ошибка: Не найден файл приватного ключа: {ssl_keyfile_path}")
        exit(1)
    if not ssl_certfile_path.exists():
        print(f"Ошибка: Не найден файл сертификата: {ssl_certfile_path}")
        exit(1)

    print("Запуск FastAPI на https://localhost:8000 с использованием SSL-сертификатов:")
    print(f"  Key: {ssl_keyfile_path}")
    print(f"  Cert: {ssl_certfile_path}")


    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        ssl_keyfile=str(ssl_keyfile_path), # uvicorn.run ожидает строку для путей
        ssl_certfile=str(ssl_certfile_path),
        reload=True,
    )

