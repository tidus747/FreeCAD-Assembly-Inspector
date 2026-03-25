"""Generate BOM command."""

from __future__ import annotations

from assembly_inspector.freecad_compat import get_active_document, show_info_message, show_warning_message
from assembly_inspector.plugin_context import get_context
from assembly_inspector.resources import get_icon_path


class GenerateBOMCommand:
    """Generate a simple BOM table from scanned parts."""

    def GetResources(self) -> dict[str, str]:  # noqa: N802
        return {
            "MenuText": "Generate BOM",
            "ToolTip": "Generate a simple BOM from current part registry",
            "Pixmap": get_icon_path("generate_bom.svg"),
        }

    def IsActive(self) -> bool:  # noqa: N802
        return get_active_document() is not None

    def Activated(self) -> None:  # noqa: N802
        context = get_context()
        rows = context.generate_bom_for_active_document()
        if not rows:
            show_warning_message("Assembly Inspector", "No BOM rows generated.")
            return

        text = context.bom_manager.rows_to_text(rows)
        preview_lines = text.splitlines()
        preview = "\n".join(preview_lines[:25])
        if len(preview_lines) > 25:
            preview += "\n..."
        preview += "\n\nSheet updated: AssemblyInspectorBOM"
        show_info_message("Assembly Inspector - BOM Preview", preview)
