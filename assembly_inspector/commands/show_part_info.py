"""Show Part Info command."""

from __future__ import annotations

from assembly_inspector.freecad_compat import get_selected_objects, show_warning_message
from assembly_inspector.plugin_context import get_context
from assembly_inspector.resources import get_icon_path


class ShowPartInfoCommand:
    """Display metadata for selected part."""

    def GetResources(self) -> dict[str, str]:  # noqa: N802
        return {
            "MenuText": "Show Part Info",
            "ToolTip": "Show metadata for the selected part",
            "Pixmap": get_icon_path("part_info.svg"),
        }

    def IsActive(self) -> bool:  # noqa: N802
        return bool(get_selected_objects())

    def Activated(self) -> None:  # noqa: N802
        context = get_context()
        record = context.get_selected_part_record()
        if record is None:
            show_warning_message(
                "Assembly Inspector",
                "No scanned part selected. Run 'Scan Assembly' first.",
            )
            return
        context.show_part_info(record)
