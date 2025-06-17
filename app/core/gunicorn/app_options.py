
def get_app_options(
    host: str,
    port: int,
    timeout: int,
    workers: int,
) -> dict:
    return {
        "bind": f"{host}:{port}",
        "timeout": timeout,
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }