"""
Root proxy package for app.
Enables 'python -m uvicorn app.main:app' to work when executed from repository root.
"""
import os
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_current_dir)
_backend_dir = os.path.join(_repo_root, "backend")

if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

_backend_app_dir = os.path.join(_backend_dir, "app")
if os.path.isdir(_backend_app_dir) and _backend_app_dir not in __path__:
    __path__.append(_backend_app_dir)

