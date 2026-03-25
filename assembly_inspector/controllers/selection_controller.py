"""Selection observer controller."""

from __future__ import annotations

from typing import Any, Callable

from assembly_inspector.freecad_compat import Gui, get_object_from_document, get_selected_objects
from assembly_inspector.logging_utils import get_logger
from assembly_inspector.models import PartRecord

LOGGER = get_logger(__name__)


class SelectionController:
    """Bridge FreeCAD selection events to plugin callbacks."""

    def __init__(
        self,
        resolve_record: Callable[[Any | None], PartRecord | None],
        on_part_selected: Callable[[PartRecord | None], None],
    ) -> None:
        self._resolve_record = resolve_record
        self._on_part_selected = on_part_selected
        self._attached = False

    def attach(self) -> None:
        """Attach as FreeCAD selection observer."""
        if Gui is None:
            LOGGER.warning("Selection observer not available without FreeCADGui")
            return
        if self._attached:
            return
        Gui.Selection.addObserver(self)
        self._attached = True
        self._emit_current_selection()
        LOGGER.info("Selection observer attached")

    def detach(self) -> None:
        """Detach observer."""
        if Gui is None or not self._attached:
            return
        Gui.Selection.removeObserver(self)
        self._attached = False
        LOGGER.info("Selection observer detached")

    # FreeCAD observer callbacks:
    def addSelection(  # noqa: N802
        self,
        doc_name: str,
        obj_name: str,
        sub_name: str | None = None,
        point: Any | None = None,
    ) -> None:
        self._emit_current_selection(doc_name, obj_name)

    def removeSelection(  # noqa: N802
        self,
        doc_name: str,
        obj_name: str,
        sub_name: str | None = None,
    ) -> None:
        self._emit_current_selection()

    def clearSelection(self, doc_name: str | None = None) -> None:  # noqa: N802
        self._on_part_selected(None)

    def setSelection(  # noqa: N802
        self,
        doc_name: str,
        obj_name: str,
        sub_name: str | None = None,
        point: Any | None = None,
    ) -> None:
        self._emit_current_selection(doc_name, obj_name)

    def _emit_current_selection(self, doc_name: str | None = None, obj_name: str | None = None) -> None:
        selected_obj = None
        if doc_name and obj_name:
            selected_obj = get_object_from_document(doc_name, obj_name)

        if selected_obj is None:
            selected = get_selected_objects()
            selected_obj = selected[0] if selected else None

        record = self._resolve_record(selected_obj)
        self._on_part_selected(record)
