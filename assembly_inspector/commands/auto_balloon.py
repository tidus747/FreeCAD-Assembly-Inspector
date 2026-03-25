"""Auto Balloon command (future-facing stub)."""

from __future__ import annotations

from assembly_inspector.freecad_compat import get_active_document, show_info_message, show_warning_message
from assembly_inspector.plugin_context import get_context
from assembly_inspector.resources import get_icon_path


class AutoBalloonCommand:
    """Best-effort TechDraw balloon automation command."""

    def GetResources(self) -> dict[str, str]:  # noqa: N802
        return {
            "MenuText": "Auto Balloon",
            "ToolTip": "Prepare automatic TechDraw balloon callouts (future)",
            "Pixmap": get_icon_path("auto_balloon.svg"),
        }

    def IsActive(self) -> bool:  # noqa: N802
        return get_active_document() is not None

    def Activated(self) -> None:  # noqa: N802
        if get_active_document() is None:
            show_warning_message("Assembly Inspector", "No active document.")
            return
        result = get_context().auto_balloon_active_document(dry_run=False)
        if not result.placements:
            details = "\n".join(result.notes) if result.notes else "No placements were planned."
            show_warning_message("Assembly Inspector", details)
            return

        lines = [
            f"Page: {result.page_name or 'N/A'}",
            f"Planned balloons: {len(result.placements)}",
            f"Created balloons: {result.created_count}",
        ]
        if result.missing_part_ids:
            lines.append(f"Missing anchors: {', '.join(result.missing_part_ids)}")
        if result.notes:
            lines.append("Notes:")
            lines.extend(result.notes)
        lines.append(
            "Note: TechDraw integration is best-effort and may require adapter tuning per FreeCAD version."
        )
        show_info_message("Assembly Inspector - Auto Balloon", "\n".join(lines))
