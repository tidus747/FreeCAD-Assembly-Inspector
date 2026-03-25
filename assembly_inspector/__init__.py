"""FreeCAD Assembly Inspector package."""


def get_context():
    """Return shared plugin context.

    Imported lazily to keep pure-logic modules testable outside FreeCAD.
    """
    from .plugin_context import get_context as _get_context

    return _get_context()


__all__ = ["get_context"]
