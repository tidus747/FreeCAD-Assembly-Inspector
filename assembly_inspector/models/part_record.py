"""Part registry model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PartRecord:
    """Normalized part data extracted from document objects."""

    part_id: str
    object_name: str
    label: str
    type_id: str | None = None
    document_name: str | None = None
    quantity: int = 1
    source_path: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_document_object(cls, obj: Any, document_name: str | None = None) -> "PartRecord":
        """Create a record from a FreeCAD-like document object."""
        object_name = str(getattr(obj, "Name", "") or "")
        label = str(getattr(obj, "Label", "") or object_name)
        type_id_value = getattr(obj, "TypeId", None)
        type_id = str(type_id_value) if type_id_value else None

        raw_part_id = (
            getattr(obj, "PartNumber", None)
            or getattr(obj, "PartNo", None)
            or getattr(obj, "PartID", None)
            or object_name
            or label
        )

        return cls(
            part_id=str(raw_part_id),
            object_name=object_name,
            label=label,
            type_id=type_id,
            document_name=document_name,
        )
