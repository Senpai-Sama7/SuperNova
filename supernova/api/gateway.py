"""Compatibility module exposing FastAPI app as `gateway:app`."""

from supernova.api.main import app

__all__ = ["app"]
