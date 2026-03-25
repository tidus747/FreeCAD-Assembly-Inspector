"""Spreadsheet-backed metadata adapter.

The Spreadsheet API details can differ by FreeCAD version. This module keeps
that uncertainty isolated and intentionally defensive.
"""

from __future__ import annotations

from typing import Any, Iterable

from assembly_inspector.logging_utils import get_logger
from assembly_inspector.models import PartRecord
from assembly_inspector.services.metadata_store import MetadataStore
from assembly_inspector.services.spreadsheet_schema import SpreadsheetSchemaManager

LOGGER = get_logger(__name__)


class SpreadsheetAdapter:
    """Low-level adapter around a FreeCAD Spreadsheet::Sheet object."""

    HEADER_PART_ID = "PartId"
    HEADER_KEY = "Key"
    HEADER_VALUE = "Value"

    def __init__(self, sheet_obj: Any) -> None:
        self._sheet = sheet_obj
        self._schema = SpreadsheetSchemaManager()
        self._last_data_row = 1

    @classmethod
    def from_document(cls, document: Any, sheet_name: str = "AssemblyInspectorMeta") -> "SpreadsheetAdapter":
        """Get or create a metadata spreadsheet from a document.

        TODO: validate behavior against target FreeCAD versions and consider
        optional transaction support when available.
        """
        if document is None:
            return cls(None)

        sheet_obj = None
        try:
            if hasattr(document, "getObject"):
                sheet_obj = document.getObject(sheet_name)
            if sheet_obj is None and hasattr(document, "addObject"):
                sheet_obj = document.addObject("Spreadsheet::Sheet", sheet_name)
        except Exception:
            LOGGER.exception("Failed to create/find spreadsheet '%s'", sheet_name)
            sheet_obj = None

        return cls(sheet_obj)

    def is_available(self) -> bool:
        """Return True when a usable spreadsheet object exists."""
        return self._sheet is not None and hasattr(self._sheet, "get") and hasattr(self._sheet, "set")

    def read_all(self) -> dict[str, dict[str, str]]:
        """Read flattened metadata rows from columns A:B:C."""
        if not self.is_available():
            return {}

        self._schema.ensure_metadata_schema(self._sheet)

        data: dict[str, dict[str, str]] = {}
        max_data_row = 1
        for row in range(2, 10000):
            part_id = str(self._safe_get(f"A{row}")).strip()
            key = str(self._safe_get(f"B{row}")).strip()
            value = str(self._safe_get(f"C{row}")).strip()

            if not part_id and not key and not value:
                break

            max_data_row = row
            if not part_id:
                continue

            part_bucket = data.setdefault(part_id, {})
            if key:
                part_bucket[key] = value

        self._last_data_row = max_data_row
        return data

    def write_all(self, data: dict[str, dict[str, str]]) -> None:
        """Write metadata rows into columns A:B:C."""
        if not self.is_available():
            raise RuntimeError("Spreadsheet adapter is not available")

        self._schema.ensure_metadata_schema(self._sheet)

        row = 2
        for part_id in sorted(data.keys()):
            metadata = data[part_id]
            if not metadata:
                self._sheet.set(f"A{row}", part_id)
                self._sheet.set(f"B{row}", "")
                self._sheet.set(f"C{row}", "")
                row += 1
                continue

            for key, value in sorted(metadata.items()):
                self._sheet.set(f"A{row}", str(part_id))
                self._sheet.set(f"B{row}", str(key))
                self._sheet.set(f"C{row}", str(value))
                row += 1

        new_last_data_row = max(1, row - 1)
        if self._last_data_row > new_last_data_row:
            self._schema.clear_rows(
                sheet=self._sheet,
                start_row=new_last_data_row + 1,
                end_row=self._last_data_row,
            )
        self._last_data_row = new_last_data_row

    def _safe_get(self, cell: str) -> str:
        try:
            value = self._sheet.get(cell)
            return "" if value is None else str(value)
        except Exception:
            return ""


class SpreadsheetMetadataStore(MetadataStore):
    """MetadataStore implementation backed by SpreadsheetAdapter."""

    def __init__(self, adapter: SpreadsheetAdapter) -> None:
        self._adapter = adapter
        self._cache: dict[str, dict[str, str]] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._cache = self._adapter.read_all()
        self._loaded = True

    def _flush(self) -> None:
        self._adapter.write_all(self._cache)

    def get_metadata(self, part_id: str) -> dict[str, str]:
        self._load()
        return dict(self._cache.get(part_id, {}))

    def set_metadata(self, part_id: str, metadata: dict[str, str]) -> None:
        self._load()
        self._cache[part_id] = {str(k): str(v) for k, v in metadata.items()}
        self._flush()

    def sync_with_records(self, records: Iterable[PartRecord]) -> None:
        self._load()
        for record in records:
            self._cache.setdefault(record.part_id, {})
        self._flush()

    def list_part_ids(self) -> list[str]:
        self._load()
        return sorted(self._cache.keys())
