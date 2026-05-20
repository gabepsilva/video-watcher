"""ASGI entrypoint for uvicorn (keeps ``vw_web.app`` import side-effect free)."""

from vw_web.app import create_app

app = create_app()
