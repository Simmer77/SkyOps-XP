"""Dedicated ASGI entrypoint for SkyOps XP to prevent process-name collisions with other FastAPI tools (e.g. XP12 WebDeck)."""
from app.main import app as skyops_app
