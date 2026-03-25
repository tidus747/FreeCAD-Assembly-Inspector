"""Compatibility helpers for optional FreeCAD and Qt imports."""

from __future__ import annotations

from typing import Any

from .logging_utils import get_logger

LOGGER = get_logger(__name__)

try:  # pragma: no cover - module exists only in FreeCAD runtime
    import FreeCAD as App
except ImportError:  # pragma: no cover
    App = None

try:  # pragma: no cover - module exists only in FreeCAD runtime
    import FreeCADGui as Gui
except ImportError:  # pragma: no cover
    Gui = None


def _get_qt_widgets() -> Any:
    """Return QtWidgets-like module for PySide/PySide2 if available."""
    try:  # pragma: no cover - depends on host runtime
        from PySide2 import QtWidgets

        return QtWidgets
    except ImportError:  # pragma: no cover
        try:
            from PySide import QtGui as QtWidgets

            return QtWidgets
        except ImportError:
            return None


def get_active_document() -> Any | None:
    """Return the active FreeCAD document if available."""
    if App is None:
        return None
    return getattr(App, "ActiveDocument", None)


def get_selected_objects() -> list[Any]:
    """Return selected objects from FreeCAD GUI."""
    if Gui is None:
        return []
    try:  # pragma: no cover - depends on GUI state
        return list(Gui.Selection.getSelection() or [])
    except Exception:
        LOGGER.exception("Failed to query current selection")
        return []


def get_object_from_document(doc_name: str, obj_name: str) -> Any | None:
    """Resolve an object by document and object name."""
    if App is None:
        return None
    try:  # pragma: no cover - depends on FreeCAD API
        document = App.getDocument(doc_name)
        if document is None:
            return None
        return document.getObject(obj_name)
    except Exception:
        LOGGER.exception("Failed to resolve object %s from document %s", obj_name, doc_name)
        return None


def show_info_message(title: str, text: str) -> None:
    """Display an informational message in GUI runtimes; log otherwise."""
    qt_widgets = _get_qt_widgets()
    if qt_widgets is None:
        LOGGER.info("%s: %s", title, text)
        return
    qt_widgets.QMessageBox.information(None, title, text)


def show_warning_message(title: str, text: str) -> None:
    """Display a warning message in GUI runtimes; log otherwise."""
    qt_widgets = _get_qt_widgets()
    if qt_widgets is None:
        LOGGER.warning("%s: %s", title, text)
        return
    qt_widgets.QMessageBox.warning(None, title, text)


def ask_save_file_path(title: str, initial_path: str, file_filter: str) -> str:
    """Prompt save-file path in GUI runtimes; return empty string if cancelled."""
    qt_widgets = _get_qt_widgets()
    if qt_widgets is None:
        return ""
    path, _ = qt_widgets.QFileDialog.getSaveFileName(
        None,
        title,
        initial_path,
        file_filter,
    )
    return str(path or "")
