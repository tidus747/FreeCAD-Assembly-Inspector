"""Tests for TechDraw auto-balloon planning."""

from assembly_inspector.models import PartRecord
from assembly_inspector.services.auto_balloon_service import AutoBalloonService
from assembly_inspector.services.bom_manager import BOMRow
from assembly_inspector.services.techdraw_adapter import BalloonAnchor, BalloonPlanner


def test_balloon_planner_avoids_collisions():
    planner = BalloonPlanner(x_offset=0.0, min_spacing=5.0, y_step=4.0)
    anchors = [
        BalloonAnchor(part_id="A", view_name="View1", x=10.0, y=10.0),
        BalloonAnchor(part_id="B", view_name="View1", x=10.0, y=10.0),
    ]
    labels = {
        "A": (1, "1"),
        "B": (2, "2"),
    }

    placements = planner.plan(anchors=anchors, labels=labels)

    assert len(placements) == 2
    assert placements[0].x == placements[1].x
    assert placements[0].y != placements[1].y


def test_auto_balloon_service_plans_and_creates(fake_document_factory, fake_parts):
    document = fake_document_factory("Asm", objects=fake_parts)
    page = document.addObject("TechDraw::DrawPage", "Page")
    view = document.addObject("TechDraw::DrawViewPart", "MainView")
    view.Source = list(fake_parts)
    view.X = 10.0
    view.Y = 15.0
    view.Width = 30.0
    view.Height = 20.0
    page.Views = [view]

    rows = [
        BOMRow(item_no=1, part_id="PartA", label="Part A", quantity=1, document_name="Asm"),
        BOMRow(item_no=2, part_id="PartB", label="Part B", quantity=1, document_name="Asm"),
    ]
    records_by_part = {
        "PartA": PartRecord.from_document_object(fake_parts[0], document_name="Asm"),
        "PartB": PartRecord.from_document_object(fake_parts[1], document_name="Asm"),
    }

    service = AutoBalloonService()
    dry_run = service.execute(document=document, rows=rows, records_by_part_id=records_by_part, dry_run=True)
    assert dry_run.page_name == "Page"
    assert len(dry_run.placements) == 2
    assert dry_run.created_count == 0

    applied = service.execute(document=document, rows=rows, records_by_part_id=records_by_part, dry_run=False)
    assert applied.created_count == 2

