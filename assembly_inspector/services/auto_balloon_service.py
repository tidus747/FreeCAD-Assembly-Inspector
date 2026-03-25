"""Service orchestrating TechDraw auto-balloon planning/execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from assembly_inspector.models import PartRecord
from assembly_inspector.services.bom_manager import BOMRow
from assembly_inspector.services.techdraw_adapter import BalloonPlanner, TechDrawAdapter


@dataclass
class AutoBalloonResult:
    """Output of auto-balloon planning/execution."""

    page_name: str | None = None
    placements: list = field(default_factory=list)
    created_count: int = 0
    missing_part_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class AutoBalloonService:
    """Compute and optionally apply TechDraw balloons."""

    def __init__(
        self,
        adapter: TechDrawAdapter | None = None,
        planner: BalloonPlanner | None = None,
    ) -> None:
        self._adapter = adapter or TechDrawAdapter()
        self._planner = planner or BalloonPlanner()

    def plan(
        self,
        document: Any,
        rows: list[BOMRow],
        records_by_part_id: dict[str, PartRecord],
    ) -> AutoBalloonResult:
        result = AutoBalloonResult()
        pages = self._adapter.find_pages(document)
        if not pages:
            result.notes.append("No TechDraw page found.")
            return result

        page = pages[0]
        result.page_name = str(getattr(page, "Name", "") or "")
        views = self._adapter.find_views(page)
        if not views:
            result.notes.append("No views found in target TechDraw page.")
            return result

        anchors = []
        labels: dict[str, tuple[int, str]] = {}
        missing: list[str] = []

        for row in rows:
            labels[row.part_id] = (row.item_no, str(row.item_no))
            record = records_by_part_id.get(row.part_id)
            if record is None:
                missing.append(row.part_id)
                continue
            anchor = self._adapter.find_anchor_for_record(views, record)
            if anchor is None:
                missing.append(row.part_id)
                continue
            anchors.append(anchor)

        result.missing_part_ids = sorted(set(missing))
        result.placements = self._planner.plan(anchors, labels)
        if not result.placements:
            result.notes.append("No balloon placements could be planned.")
        return result

    def execute(
        self,
        document: Any,
        rows: list[BOMRow],
        records_by_part_id: dict[str, PartRecord],
        dry_run: bool = False,
    ) -> AutoBalloonResult:
        result = self.plan(document=document, rows=rows, records_by_part_id=records_by_part_id)
        if dry_run:
            return result
        if not result.page_name:
            return result

        page = next(
            (item for item in self._adapter.find_pages(document) if str(getattr(item, "Name", "") or "") == result.page_name),
            None,
        )
        if page is None:
            result.notes.append("Planned page is no longer available.")
            return result

        created = 0
        for placement in result.placements:
            obj = self._adapter.create_balloon(page, placement)
            if obj is not None:
                created += 1
        result.created_count = created
        if created < len(result.placements):
            result.notes.append("Some balloons could not be created due to API/runtime constraints.")
        return result

