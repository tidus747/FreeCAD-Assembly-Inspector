"""Shared runtime context for the workbench."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from assembly_inspector.controllers import SelectionController
from assembly_inspector.freecad_compat import get_active_document, get_selected_objects
from assembly_inspector.logging_utils import get_logger
from assembly_inspector.models import PartRecord
from assembly_inspector.services import (
    AutoBalloonResult,
    AutoBalloonService,
    AssemblyScanner,
    BOMExporter,
    BOMManager,
    FallbackMetadataStore,
    InMemoryMetadataStore,
    MetadataStore,
    SpreadsheetAdapter,
    SpreadsheetMetadataStore,
)
from assembly_inspector.ui import update_or_create_dialog

LOGGER = get_logger(__name__)


@dataclass
class PluginContext:
    """State container shared by commands and controllers."""

    scanner: AssemblyScanner = field(default_factory=AssemblyScanner)
    bom_manager: BOMManager = field(default_factory=BOMManager)
    bom_exporter: BOMExporter = field(default_factory=BOMExporter)
    auto_balloon_service: AutoBalloonService = field(default_factory=AutoBalloonService)
    metadata_store: MetadataStore = field(default_factory=InMemoryMetadataStore)
    registry: dict[str, PartRecord] = field(default_factory=dict)
    _bound_document_name: str | None = None
    _selection_controller: SelectionController | None = None
    _info_dialog: Any | None = None

    def initialize(self) -> None:
        """Initialize context internals."""
        if self._selection_controller is None:
            self._selection_controller = SelectionController(
                resolve_record=self.resolve_record_from_object,
                on_part_selected=self.on_part_selected,
            )

    def attach_selection_observer(self) -> None:
        """Enable automatic part info updates on selection changes."""
        self.initialize()
        if self._selection_controller:
            self._selection_controller.attach()

    def detach_selection_observer(self) -> None:
        """Disable automatic part info updates."""
        if self._selection_controller:
            self._selection_controller.detach()

    def _ensure_metadata_store_for_document(self, document: Any) -> None:
        doc_name = str(getattr(document, "Name", "") or "")
        if not doc_name or doc_name == self._bound_document_name:
            return

        in_memory = InMemoryMetadataStore()
        adapter = SpreadsheetAdapter.from_document(document)
        if adapter.is_available():
            spreadsheet_store = SpreadsheetMetadataStore(adapter)
            self.metadata_store = FallbackMetadataStore(
                primary=spreadsheet_store,
                fallback=in_memory,
            )
            LOGGER.info("Using spreadsheet-backed metadata store for '%s'", doc_name)
        else:
            self.metadata_store = in_memory
            LOGGER.info("Using in-memory metadata store for '%s'", doc_name)

        self._bound_document_name = doc_name

    def scan_active_document(self) -> list[PartRecord]:
        """Scan active document and refresh registry."""
        document = get_active_document()
        if document is None:
            LOGGER.warning("No active document to scan")
            return []
        return self.scan_document(document)

    def scan_document(self, document: Any) -> list[PartRecord]:
        """Scan a specific document object and refresh registry."""
        self._ensure_metadata_store_for_document(document)
        records = self.scanner.scan_document(document)
        self.registry = {record.object_name: record for record in records}
        self.metadata_store.sync_with_records(records)
        return records

    def resolve_record_from_object(self, obj: Any | None) -> PartRecord | None:
        """Resolve one selected object to a scanned part record."""
        if obj is None:
            return None

        object_name = str(getattr(obj, "Name", "") or "")
        if object_name and object_name in self.registry:
            return self.registry[object_name]

        # Fallback on part id lookup for linked/derived objects.
        part_id = str(
            getattr(obj, "PartNumber", None)
            or getattr(obj, "PartNo", None)
            or getattr(obj, "PartID", None)
            or ""
        )
        if part_id:
            for record in self.registry.values():
                if record.part_id == part_id:
                    return record
        return None

    def get_selected_part_record(self) -> PartRecord | None:
        """Return first scanned record from current selection."""
        selected = get_selected_objects()
        if not selected:
            return None
        return self.resolve_record_from_object(selected[0])

    def on_part_selected(self, record: PartRecord | None) -> None:
        """Selection callback used by SelectionController."""
        if record is None:
            return
        metadata = self.metadata_store.get_metadata(record.part_id)
        self._info_dialog = update_or_create_dialog(
            record=record,
            metadata=metadata,
            dialog=self._info_dialog,
            on_save=self.save_part_metadata,
        )

    def show_part_info(self, record: PartRecord) -> None:
        """Show info panel for one part."""
        metadata = self.metadata_store.get_metadata(record.part_id)
        self._info_dialog = update_or_create_dialog(
            record=record,
            metadata=metadata,
            dialog=self._info_dialog,
            on_save=self.save_part_metadata,
        )

    def save_part_metadata(self, part_id: str, metadata: dict[str, str]) -> None:
        """Persist metadata and keep dialog in sync."""
        self.metadata_store.set_metadata(part_id, metadata)
        for record in self.registry.values():
            if record.part_id == part_id:
                self.show_part_info(record)
                break

    def generate_bom_for_active_document(self) -> list:
        """Generate BOM rows for active document."""
        document = get_active_document()
        if document is None:
            LOGGER.warning("No active document for BOM generation")
            return []

        document_name = str(getattr(document, "Name", "") or "")
        if not self.registry or self._bound_document_name != document_name:
            self.scan_document(document)

        rows = self.bom_manager.generate_rows(
            records=self.registry.values(),
            metadata_store=self.metadata_store,
        )
        self.bom_exporter.write_to_document_spreadsheet(document=document, rows=rows)
        return rows

    def export_bom_csv(self, path: str | Path) -> Path | None:
        """Export active BOM to CSV."""
        rows = self.generate_bom_for_active_document()
        if not rows:
            return None
        return self.bom_exporter.export_csv(rows=rows, path=path)

    def export_bom_xlsx(self, path: str | Path) -> Path | None:
        """Export active BOM to XLSX."""
        rows = self.generate_bom_for_active_document()
        if not rows:
            return None
        return self.bom_exporter.export_xlsx(rows=rows, path=path)

    def auto_balloon_active_document(self, dry_run: bool = False) -> AutoBalloonResult:
        """Plan/apply TechDraw balloons for current document."""
        document = get_active_document()
        if document is None:
            return AutoBalloonResult(notes=["No active document."])

        rows = self.generate_bom_for_active_document()
        if not rows:
            return AutoBalloonResult(notes=["No BOM rows available for ballooning."])

        records_by_part_id = self._records_by_part_id()
        return self.auto_balloon_service.execute(
            document=document,
            rows=rows,
            records_by_part_id=records_by_part_id,
            dry_run=dry_run,
        )

    def _records_by_part_id(self) -> dict[str, PartRecord]:
        mapping: dict[str, PartRecord] = {}
        for record in self.registry.values():
            mapping.setdefault(record.part_id, record)
        return mapping


_CONTEXT = PluginContext()


def get_context() -> PluginContext:
    """Return singleton plugin context."""
    return _CONTEXT
