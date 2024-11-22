"""
Makes the UI directory a Python package and exposes the main UI builder.
"""

from .main import get_main_ui

__all__ = ["get_main_ui"]
