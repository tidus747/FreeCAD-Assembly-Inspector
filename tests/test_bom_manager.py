"""Tests for BOMManager."""

from assembly_inspector.models import PartRecord
from assembly_inspector.services.bom_manager import BOMManager
from assembly_inspector.services.metadata_store import InMemoryMetadataStore


def test_bom_rows_group_by_part_id():
    manager = BOMManager()
    store = InMemoryMetadataStore()
    store.set_metadata("A-001", {"Desc": "Plate"})

    records = [
        PartRecord(part_id="A-001", object_name="Obj1", label="Plate"),
        PartRecord(part_id="A-001", object_name="Obj2", label="Plate"),
        PartRecord(part_id="B-010", object_name="Obj3", label="Spacer"),
    ]

    rows = manager.generate_rows(records, metadata_store=store)

    assert len(rows) == 2
    assert rows[0].part_id == "A-001"
    assert rows[0].quantity == 2
    assert rows[0].metadata["Desc"] == "Plate"
    assert rows[1].part_id == "B-010"
    assert rows[1].quantity == 1


def test_rows_to_text_contains_header_and_rows():
    manager = BOMManager()
    rows = manager.generate_rows(
        [
            PartRecord(part_id="C-100", object_name="ObjC", label="Cover"),
        ]
    )

    text = manager.rows_to_text(rows)

    assert "Item\tPartId\tLabel\tQty\tDocument" in text
    assert "C-100" in text

