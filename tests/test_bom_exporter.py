"""Tests for BOMExporter."""

from __future__ import annotations

from pathlib import Path

import pytest

from assembly_inspector.services.bom_exporter import BOMExporter
from assembly_inspector.services.bom_manager import BOMRow


def test_export_csv_writes_file(tmp_path: Path):
    exporter = BOMExporter()
    rows = [
        BOMRow(item_no=1, part_id="A-001", label="Plate", quantity=2, document_name="Asm"),
    ]

    out_file = exporter.export_csv(rows, tmp_path / "bom.csv")

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "PartId" in content
    assert "A-001" in content


def test_write_to_document_spreadsheet(fake_document_factory):
    exporter = BOMExporter()
    document = fake_document_factory("Asm")
    rows = [
        BOMRow(item_no=1, part_id="P-001", label="Base", quantity=1, document_name="Asm"),
        BOMRow(item_no=2, part_id="P-002", label="Cover", quantity=3, document_name="Asm"),
    ]

    ok = exporter.write_to_document_spreadsheet(document=document, rows=rows)

    assert ok is True
    sheet = document.getObject("AssemblyInspectorBOM")
    assert sheet.get("A1") == "Item"
    assert sheet.get("B1") == "PartId"
    assert sheet.get("B2") == "P-001"
    assert sheet.get("B3") == "P-002"


def test_export_xlsx_optional_dependency(tmp_path: Path):
    exporter = BOMExporter()
    rows = [
        BOMRow(item_no=1, part_id="X-1", label="Widget", quantity=1, document_name="Asm"),
    ]

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError):
            exporter.export_xlsx(rows, tmp_path / "bom.xlsx")
    else:
        output = exporter.export_xlsx(rows, tmp_path / "bom.xlsx")
        assert output.exists()

