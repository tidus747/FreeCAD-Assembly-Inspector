"""Tests for AssemblyScanner."""

from assembly_inspector.services.assembly_scanner import AssemblyScanner


class FakeObject:
    """Simple FreeCAD-like object."""

    def __init__(self, name, label, type_id, shape=None, linked_object=None):
        self.Name = name
        self.Label = label
        self.TypeId = type_id
        self.Shape = shape
        self.LinkedObject = linked_object


class FakeDocument:
    """Simple FreeCAD-like document."""

    def __init__(self, name, objects):
        self.Name = name
        self.Objects = objects


def test_scan_document_collects_relevant_objects():
    document = FakeDocument(
        name="Asm",
        objects=[
            FakeObject("Part001", "Part 001", "Part::Feature"),
            FakeObject("Ignore001", "Ignore", "App::DocumentObjectGroup"),
            FakeObject("Link001", "Linked", "App::Link"),
        ],
    )

    scanner = AssemblyScanner()
    records = scanner.scan_document(document)

    assert [record.object_name for record in records] == ["Part001", "Link001"]
    assert [record.part_id for record in records] == ["Part001", "Link001"]


def test_scan_document_accepts_shape_based_object_without_type_prefix():
    document = FakeDocument(
        name="Asm",
        objects=[
            FakeObject("Body001", "Body 001", "Custom::Proxy", shape=object()),
        ],
    )

    scanner = AssemblyScanner()
    records = scanner.scan_document(document)

    assert len(records) == 1
    assert records[0].object_name == "Body001"

