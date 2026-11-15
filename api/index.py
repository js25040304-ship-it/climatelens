"""Vercel entry point: exposes the FastAPI app as one Python serverless function."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402  (path setup must run first)

# Vercel's Python runtime picks up this module-level ASGI callable.
