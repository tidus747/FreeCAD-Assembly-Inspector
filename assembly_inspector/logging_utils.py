"""Logging helpers for the workbench."""

from __future__ import annotations

import logging
import sys
from typing import Any

_LOGGING_CONFIGURED = False
_PACKAGE_LOGGER_NAME = "assembly_inspector"


class _FreeCADConsoleHandler(logging.Handler):
    """Write logs to FreeCAD console when available."""

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        if not message.endswith("\n"):
            message += "\n"

        console = _get_freecad_console()
        if console is not None:
            try:
                if record.levelno >= logging.ERROR and hasattr(console, "PrintError"):
                    console.PrintError(message)
                    return
                if record.levelno >= logging.WARNING and hasattr(console, "PrintWarning"):
                    console.PrintWarning(message)
                    return
                if hasattr(console, "PrintMessage"):
                    console.PrintMessage(message)
                    return
            except Exception:
                pass

        stream = sys.stderr if record.levelno >= logging.WARNING else sys.stdout
        if stream is not None and hasattr(stream, "write"):
            stream.write(message)


def _get_freecad_console() -> Any | None:
    try:  # pragma: no cover - only available in FreeCAD runtime
        import FreeCAD as App

        return getattr(App, "Console", None)
    except ImportError:
        return None


def configure_logging(level: int = logging.INFO) -> None:
    """Configure package logger once, avoiding broken host stderr streams."""
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    package_logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    package_logger.setLevel(level)
    package_logger.handlers.clear()
    package_logger.propagate = False

    handler: logging.Handler = _FreeCADConsoleHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    package_logger.addHandler(handler)

    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger with package configuration enabled."""
    configure_logging()
    return logging.getLogger(name)
