"""TechDraw adapters and placement primitives.

The TechDraw API can vary across FreeCAD versions. This adapter intentionally
uses conservative introspection and keeps uncertain integration in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from assembly_inspector.logging_utils import get_logger
from assembly_inspector.models import PartRecord

LOGGER = get_logger(__name__)


@dataclass
class BalloonAnchor:
    """Anchor candidate for a BOM item."""

    part_id: str
    view_name: str
    x: float
    y: float


@dataclass
class BalloonPlacement:
    """Resolved label placement."""

    item_no: int
    part_id: str
    label: str
    view_name: str
    x: float
    y: float


class TechDrawAdapter:
    """Read/write facade for TechDraw entities."""

    def find_pages(self, document: Any) -> list[Any]:
        if document is None:
            return []
        objects = getattr(document, "Objects", []) or []
        pages = []
        for obj in objects:
            type_id = str(getattr(obj, "TypeId", "") or "")
            if type_id.startswith("TechDraw::DrawPage"):
                pages.append(obj)
        return pages

    def find_views(self, page: Any) -> list[Any]:
        if page is None:
            return []
        views = list(getattr(page, "Views", []) or [])
        if views:
            return views
        # Some builds may expose views in a different property name.
        return list(getattr(page, "ViewObjects", []) or [])

    def find_anchor_for_record(self, views: Iterable[Any], record: PartRecord) -> BalloonAnchor | None:
        """Find one best-effort anchor for a record.

        TODO: Replace this heuristic with geometric anchor extraction once
        stable APIs for projected edge/vertex mapping are confirmed.
        """
        for view in views:
            if self._view_references_record(view, record):
                x, y = self._view_center(view)
                return BalloonAnchor(
                    part_id=record.part_id,
                    view_name=str(getattr(view, "Name", "") or ""),
                    x=x,
                    y=y,
                )
        return None

    def create_balloon(self, page: Any, placement: BalloonPlacement) -> Any | None:
        """Attempt to create one balloon annotation on a page.

        This is a guarded best-effort implementation because exact TechDraw
        annotation classes and property names may differ across versions.
        """
        document = getattr(page, "Document", None)
        if document is None or not hasattr(document, "addObject"):
            LOGGER.warning("No document/addObject available for TechDraw balloon creation")
            return None

        try:
            name = f"AI_Balloon_{placement.item_no}"
            balloon = document.addObject("TechDraw::DrawViewAnnotation", name)
        except Exception:
            LOGGER.exception("Failed creating TechDraw annotation object")
            return None

        # Best effort property assignment.
        for prop, value in (
            ("Text", placement.label),
            ("X", placement.x),
            ("Y", placement.y),
        ):
            try:
                if hasattr(balloon, prop):
                    setattr(balloon, prop, value)
            except Exception:
                LOGGER.debug("Could not set %s on balloon", prop)

        try:
            if hasattr(page, "addView"):
                page.addView(balloon)
        except Exception:
            LOGGER.debug("Could not attach balloon to page via addView")

        return balloon

    @staticmethod
    def _view_references_record(view: Any, record: PartRecord) -> bool:
        sources = []
        for attr in ("Source", "Sources", "SourceObjects"):
            raw = getattr(view, attr, None)
            if raw is None:
                continue
            if isinstance(raw, (list, tuple)):
                sources.extend(raw)
            else:
                sources.append(raw)

        for source in sources:
            name = str(getattr(source, "Name", "") or "")
            label = str(getattr(source, "Label", "") or "")
            if name == record.object_name or label == record.label:
                return True
        return False

    @staticmethod
    def _view_center(view: Any) -> tuple[float, float]:
        x = float(getattr(view, "X", 0.0) or 0.0)
        y = float(getattr(view, "Y", 0.0) or 0.0)
        width = float(getattr(view, "Width", 0.0) or 0.0)
        height = float(getattr(view, "Height", 0.0) or 0.0)
        if width > 0:
            x += width / 2.0
        if height > 0:
            y += height / 2.0
        return x, y


class BalloonPlanner:
    """Simple collision-avoidance planner for callout labels."""

    def __init__(self, x_offset: float = 12.0, min_spacing: float = 8.0, y_step: float = 6.0) -> None:
        self._x_offset = float(x_offset)
        self._min_spacing = float(min_spacing)
        self._y_step = float(y_step)

    def plan(self, anchors: list[BalloonAnchor], labels: dict[str, tuple[int, str]]) -> list[BalloonPlacement]:
        placements: list[BalloonPlacement] = []
        occupied: list[tuple[float, float]] = []

        for anchor in sorted(anchors, key=lambda item: (item.view_name, item.y, item.x)):
            item_info = labels.get(anchor.part_id)
            if item_info is None:
                continue
            item_no, label = item_info
            x = anchor.x + self._x_offset
            y = anchor.y
            while self._collides(x, y, occupied):
                y += self._y_step
            occupied.append((x, y))
            placements.append(
                BalloonPlacement(
                    item_no=item_no,
                    part_id=anchor.part_id,
                    label=label,
                    view_name=anchor.view_name,
                    x=x,
                    y=y,
                )
            )
        return placements

    def _collides(self, x: float, y: float, occupied: list[tuple[float, float]]) -> bool:
        for ox, oy in occupied:
            if abs(ox - x) < self._min_spacing and abs(oy - y) < self._min_spacing:
                return True
        return False

