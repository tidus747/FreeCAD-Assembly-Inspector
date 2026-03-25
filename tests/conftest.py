"""Shared test fixtures for integration-like tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class FakeObject:
    """Generic FreeCAD-like object."""

    Name: str
    Label: str
    TypeId: str
    Document: Any | None = None
    Shape: Any | None = None
    LinkedObject: Any | None = None
    Views: list[Any] = field(default_factory=list)
    Source: list[Any] = field(default_factory=list)
    X: float = 0.0
    Y: float = 0.0
    Width: float = 0.0
    Height: float = 0.0
    Text: str = ""

    def addView(self, view: Any) -> None:
        self.Views.append(view)


class FakeSheet:
    """Spreadsheet-like object with cell map."""

    TypeId = "Spreadsheet::Sheet"

    def __init__(self, name: str) -> None:
        self.Name = name
        self.Label = name
        self._cells: dict[str, str] = {}

    def get(self, cell: str) -> str:
        return self._cells.get(cell, "")

    def set(self, cell: str, value: str) -> None:
        self._cells[cell] = str(value)


class FakeDocument:
    """Document-like test double supporting getObject/addObject."""

    def __init__(self, name: str, objects: list[Any] | None = None) -> None:
        self.Name = name
        self.Objects: list[Any] = list(objects or [])
        self._map: dict[str, Any] = {obj.Name: obj for obj in self.Objects if hasattr(obj, "Name")}
        for obj in self.Objects:
            if getattr(obj, "Document", None) is None:
                obj.Document = self
        self.recomputed = False

    def getObject(self, name: str) -> Any | None:  # noqa: N802
        return self._map.get(name)

    def addObject(self, type_id: str, name: str) -> Any:  # noqa: N802
        if type_id == "Spreadsheet::Sheet":
            obj = FakeSheet(name)
        else:
            obj = FakeObject(Name=name, Label=name, TypeId=type_id)
        obj.Document = self
        self.Objects.append(obj)
        self._map[name] = obj
        return obj

    def recompute(self) -> None:
        self.recomputed = True


@pytest.fixture
def fake_document_factory():
    """Create FakeDocument instances."""

    def _factory(name: str, objects: list[Any] | None = None) -> FakeDocument:
        return FakeDocument(name=name, objects=objects)

    return _factory


@pytest.fixture
def fake_parts() -> list[FakeObject]:
    """Provide a minimal part list."""
    return [
        FakeObject(Name="PartA", Label="Part A", TypeId="Part::Feature"),
        FakeObject(Name="PartB", Label="Part B", TypeId="Part::Feature"),
    ]

