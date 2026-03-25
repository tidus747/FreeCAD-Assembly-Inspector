"""Scan Assembly command."""

from __future__ import annotations

from assembly_inspector.freecad_compat import get_active_document, show_info_message, show_warning_message
from assembly_inspector.plugin_context import get_context
from assembly_inspector.resources import get_icon_path


class ScanAssemblyCommand:
    """Collect assembly objects and refresh the part registry."""

    def GetResources(self) -> dict[str, str]:  # noqa: N802
        return {
            "MenuText": "Scan Assembly",
            "ToolTip": "Scan active document and refresh part registry",
            "Pixmap": get_icon_path("scan_assembly.svg"),
        }

    def IsActive(self) -> bool:  # noqa: N802
        return get_active_document() is not None

    def Activated(self) -> None:  # noqa: N802
        context = get_context()
        records = context.scan_active_document()
        if not records:
            show_warning_message("Assembly Inspector", "No eligible part objects found.")
            return
        show_info_message(
            "Assembly Inspector",
            f"Assembly scan complete. {len(records)} part records available.",
        )
