"""Export BOM CSV command."""

from __future__ import annotations

from pathlib import Path

from assembly_inspector.freecad_compat import (
    ask_save_file_path,
    get_active_document,
    show_info_message,
    show_warning_message,
)
from assembly_inspector.plugin_context import get_context
from assembly_inspector.resources import get_icon_path


class ExportBOMCsvCommand:
    """Export current BOM rows to CSV file."""

    def GetResources(self) -> dict[str, str]:  # noqa: N802
        return {
            "MenuText": "Export BOM CSV",
            "ToolTip": "Export BOM as CSV file",
            "Pixmap": get_icon_path("export_csv.svg"),
        }

    def IsActive(self) -> bool:  # noqa: N802
        return get_active_document() is not None

    def Activated(self) -> None:  # noqa: N802
        context = get_context()
        document = get_active_document()
        default_name = f"{getattr(document, 'Name', 'assembly')}_bom.csv" if document else "assembly_bom.csv"
        target = ask_save_file_path(
            title="Export BOM CSV",
            initial_path=str(Path.home() / default_name),
            file_filter="CSV files (*.csv)",
        )
        if not target:
            return

        try:
            path = context.export_bom_csv(target)
        except Exception as exc:  # pragma: no cover - runtime dependent
            show_warning_message("Assembly Inspector", f"CSV export failed: {exc}")
            return
        if path is None:
            show_warning_message("Assembly Inspector", "No BOM rows to export.")
            return
        show_info_message("Assembly Inspector", f"BOM exported to:\n{path}")
