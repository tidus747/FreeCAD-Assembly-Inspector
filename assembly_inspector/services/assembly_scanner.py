"""Assembly scanning service."""

from __future__ import annotations

from typing import Any, Iterable

from assembly_inspector.logging_utils import get_logger
from assembly_inspector.models import PartRecord

LOGGER = get_logger(__name__)


class AssemblyScanner:
    """Scan FreeCAD-like documents and extract part records."""

    DEFAULT_TYPE_PREFIXES = (
        "App::Part",
        "App::Link",
        "Assembly::",
        "Part::",
        "PartDesign::",
    )

    def __init__(self, type_prefixes: Iterable[str] | None = None) -> None:
        self._type_prefixes = tuple(type_prefixes or self.DEFAULT_TYPE_PREFIXES)

    def scan_document(self, document: Any) -> list[PartRecord]:
        """Extract normalized part records from a document object."""
        if document is None:
            LOGGER.warning("scan_document called with no document")
            return []

        document_name = str(getattr(document, "Name", "") or "")
        raw_objects = getattr(document, "Objects", []) or []
        records: list[PartRecord] = []
        seen_object_names: set[str] = set()

        for obj in raw_objects:
            if not self.is_relevant_object(obj):
                continue

            record = PartRecord.from_document_object(obj, document_name=document_name)
            if not record.object_name:
                continue
            if record.object_name in seen_object_names:
                continue

            seen_object_names.add(record.object_name)
            records.append(record)

        LOGGER.info(
            "Assembly scan completed for document '%s': %d part records",
            document_name,
            len(records),
        )
        return records

    def is_relevant_object(self, obj: Any) -> bool:
        """Heuristic filter for part-like document objects.

        TODO: replace with a tighter object policy once assembly APIs are stable
        across FreeCAD versions.
        """
        type_id = str(getattr(obj, "TypeId", "") or "")
        if type_id and type_id.startswith(self._type_prefixes):
            return True

        if getattr(obj, "Shape", None) is not None:
            return True

        if getattr(obj, "LinkedObject", None) is not None:
            return True

        return False

