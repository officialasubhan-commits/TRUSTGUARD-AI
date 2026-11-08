"""
Root-level ASGI application entrypoint for Render and cloud hosts.
Forwards execution to backend.app.main:app.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app  # noqa: E402

__all__ = ["app"]

