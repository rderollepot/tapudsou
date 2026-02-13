from __future__ import annotations

"""Core package for the Tapudsou lunch card monitor.

This package exposes the main library entrypoints used by the CLI and
scheduled jobs.
"""

from .core import run_check  # noqa: F401

__all__ = ["run_check"]

