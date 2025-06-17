__all__ = (
    "main_app",
    "main",
)

from core.config import settings
from core.gunicorn import Application, get_app_options
from main import app


def main():
    Application(
        application=app,
        options=get_app_options(
            host=settings.gunicorn.host,
            port=settings.gunicorn.port,
            timeout=settings.gunicorn.timeout,
            workers=settings.gunicorn.workers,
        ),
    ).run()


if __name__ == "__main__":
    main()