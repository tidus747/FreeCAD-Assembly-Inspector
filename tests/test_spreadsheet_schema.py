"""Tests for spreadsheet schema and adapter behaviors."""

from assembly_inspector.services.spreadsheet_adapter import SpreadsheetAdapter


def test_spreadsheet_adapter_initializes_schema_marker(fake_document_factory):
    document = fake_document_factory("Asm")
    adapter = SpreadsheetAdapter.from_document(document)

    assert adapter.is_available()
    _ = adapter.read_all()

    sheet = document.getObject("AssemblyInspectorMeta")
    assert sheet.get("A1") == "PartId"
    assert sheet.get("B1") == "Key"
    assert sheet.get("C1") == "Value"
    assert sheet.get("Z1") == "AssemblyInspectorSchema=1"


def test_spreadsheet_adapter_clears_stale_rows_on_write(fake_document_factory):
    document = fake_document_factory("Asm")
    adapter = SpreadsheetAdapter.from_document(document)
    sheet = document.getObject("AssemblyInspectorMeta")

    adapter.write_all({"P-1": {"Material": "Steel"}})
    assert sheet.get("A2") == "P-1"
    assert sheet.get("B2") == "Material"
    assert sheet.get("C2") == "Steel"

    adapter.write_all({})

    assert sheet.get("A2") == ""
    assert sheet.get("B2") == ""
    assert sheet.get("C2") == ""


def test_spreadsheet_adapter_migrates_legacy_sheet(fake_document_factory):
    document = fake_document_factory("Asm")
    adapter = SpreadsheetAdapter.from_document(document)
    sheet = document.getObject("AssemblyInspectorMeta")

    # Simulate legacy data without marker and non-standard headers.
    sheet.set("A1", "OldHeader")
    sheet.set("A2", "P-2")
    sheet.set("B2", "Finish")
    sheet.set("C2", "Anodized")

    data = adapter.read_all()

    assert data["P-2"]["Finish"] == "Anodized"
    assert sheet.get("A1") == "PartId"
    assert sheet.get("Z1") == "AssemblyInspectorSchema=1"

