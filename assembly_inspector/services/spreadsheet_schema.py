"""Spreadsheet schema management and migrations.

This module centralizes schema/version handling so spreadsheet API uncertainty
is isolated behind one adapter.
"""

from __future__ import annotations

from typing import Any, Iterable

from assembly_inspector.logging_utils import get_logger

LOGGER = get_logger(__name__)


class SpreadsheetSchemaManager:
    """Handle schema versioning and lightweight migrations."""

    CURRENT_VERSION = 1
    METADATA_HEADERS = ("PartId", "Key", "Value")
    SCHEMA_MARKER_CELL = "Z1"
    SCHEMA_MARKER_PREFIX = "AssemblyInspectorSchema="

    def ensure_metadata_schema(self, sheet: Any) -> int:
        """Validate/migrate schema and return final version.

        Version strategy:
        - v0: no marker. Existing A/B/C data may already exist.
        - v1: marker in ``Z1`` and canonical A1/B1/C1 headers.
        """
        if sheet is None:
            return 0

        version = self.detect_version(sheet)
        self._ensure_headers(sheet)

        if version < 1:
            self._migrate_v0_to_v1(sheet)
            version = 1

        self._write_version(sheet, self.CURRENT_VERSION)
        return self.CURRENT_VERSION

    def detect_version(self, sheet: Any) -> int:
        """Read schema version marker."""
        if sheet is None:
            return 0

        marker = self._safe_get(sheet, self.SCHEMA_MARKER_CELL)
        if not marker.startswith(self.SCHEMA_MARKER_PREFIX):
            return 0

        value = marker.replace(self.SCHEMA_MARKER_PREFIX, "", 1).strip()
        try:
            return int(value)
        except ValueError:
            return 0

    def clear_rows(
        self,
        sheet: Any,
        start_row: int,
        end_row: int,
        columns: Iterable[str] = ("A", "B", "C"),
    ) -> None:
        """Clear a row range for given columns."""
        if sheet is None or end_row < start_row:
            return
        for row in range(start_row, end_row + 1):
            for col in columns:
                self._safe_set(sheet, f"{col}{row}", "")

    def _ensure_headers(self, sheet: Any) -> None:
        expected = self.METADATA_HEADERS
        cells = ("A1", "B1", "C1")
        for cell, value in zip(cells, expected):
            current = self._safe_get(sheet, cell)
            if current != value:
                self._safe_set(sheet, cell, value)

    def _migrate_v0_to_v1(self, sheet: Any) -> None:
        """Migration hook for legacy sheets without marker."""
        # Existing data in A/B/C is retained. We only standardize headers.
        self._ensure_headers(sheet)
        LOGGER.info("Migrated metadata spreadsheet schema from v0 to v1")

    def _write_version(self, sheet: Any, version: int) -> None:
        self._safe_set(sheet, self.SCHEMA_MARKER_CELL, f"{self.SCHEMA_MARKER_PREFIX}{version}")

    @staticmethod
    def _safe_get(sheet: Any, cell: str) -> str:
        try:
            value = sheet.get(cell)
            return "" if value is None else str(value).strip()
        except Exception:
            return ""

    @staticmethod
    def _safe_set(sheet: Any, cell: str, value: str) -> None:
        try:
            sheet.set(cell, str(value))
        except Exception:
            LOGGER.exception("Failed setting spreadsheet cell %s", cell)

