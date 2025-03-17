from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from starlette.middleware.authentication import AuthenticationMiddleware

from src.routers.middlewares import JWTAuthMiddleware, JWTErrorHandlingMiddleware
from src.routers.auth import authe
from src.routers.get import gets
from src.logics.gameM import game

from src.utils.config import settings

"""



"""

origins = [
    settings.get_cors_conf()["http_cors"],
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app = FastAPI()

app.add_middleware(AuthenticationMiddleware, backend=JWTAuthMiddleware())
app.add_middleware(JWTErrorHandlingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

app.include_router(authe,prefix="/api")
app.include_router(gets,prefix="/api")
app.include_router(game,prefix="/api")


