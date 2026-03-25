"""Integration-style tests for command activation with fake documents."""

from __future__ import annotations

from pathlib import Path

from assembly_inspector.commands.auto_balloon import AutoBalloonCommand
from assembly_inspector.commands.export_bom_csv import ExportBOMCsvCommand
from assembly_inspector.commands.generate_bom import GenerateBOMCommand
from assembly_inspector.commands.scan_assembly import ScanAssemblyCommand
from assembly_inspector.commands.show_part_info import ShowPartInfoCommand
from assembly_inspector.plugin_context import PluginContext


def test_scan_show_and_generate_commands_work_with_fixture_document(
    monkeypatch,
    fake_document_factory,
    fake_parts,
):
    document = fake_document_factory("Asm", objects=fake_parts)
    context = PluginContext()
    shown_records = []
    info_messages = []
    warning_messages = []

    monkeypatch.setattr("assembly_inspector.plugin_context.get_active_document", lambda: document)
    monkeypatch.setattr("assembly_inspector.plugin_context.get_selected_objects", lambda: [fake_parts[0]])
    monkeypatch.setattr("assembly_inspector.commands.scan_assembly.get_context", lambda: context)
    monkeypatch.setattr("assembly_inspector.commands.show_part_info.get_context", lambda: context)
    monkeypatch.setattr("assembly_inspector.commands.generate_bom.get_context", lambda: context)
    monkeypatch.setattr(
        context,
        "show_part_info",
        lambda record: shown_records.append(record),
    )

    monkeypatch.setattr(
        "assembly_inspector.commands.scan_assembly.show_info_message",
        lambda title, text: info_messages.append((title, text)),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.scan_assembly.show_warning_message",
        lambda title, text: warning_messages.append((title, text)),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.show_part_info.show_warning_message",
        lambda title, text: warning_messages.append((title, text)),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.generate_bom.show_info_message",
        lambda title, text: info_messages.append((title, text)),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.generate_bom.show_warning_message",
        lambda title, text: warning_messages.append((title, text)),
    )

    ScanAssemblyCommand().Activated()
    ShowPartInfoCommand().Activated()
    GenerateBOMCommand().Activated()

    assert len(context.registry) == 2
    assert len(shown_records) == 1
    assert shown_records[0].object_name == "PartA"
    assert document.getObject("AssemblyInspectorBOM") is not None
    assert any("Assembly scan complete" in text for _, text in info_messages)
    assert any("Sheet updated: AssemblyInspectorBOM" in text for _, text in info_messages)
    assert warning_messages == []


def test_export_and_auto_balloon_commands_with_document_fixture(
    monkeypatch,
    tmp_path: Path,
    fake_document_factory,
    fake_parts,
):
    document = fake_document_factory("Asm", objects=fake_parts)
    page = document.addObject("TechDraw::DrawPage", "Page")
    view = document.addObject("TechDraw::DrawViewPart", "MainView")
    view.Source = list(fake_parts)
    view.X = 10.0
    view.Y = 10.0
    view.Width = 20.0
    view.Height = 10.0
    page.Views = [view]

    context = PluginContext()
    context.scan_document(document)
    info_messages = []
    warning_messages = []

    csv_path = tmp_path / "bom.csv"
    monkeypatch.setattr("assembly_inspector.plugin_context.get_active_document", lambda: document)
    monkeypatch.setattr("assembly_inspector.commands.export_bom_csv.get_context", lambda: context)
    monkeypatch.setattr("assembly_inspector.commands.auto_balloon.get_context", lambda: context)
    monkeypatch.setattr("assembly_inspector.commands.export_bom_csv.get_active_document", lambda: document)
    monkeypatch.setattr("assembly_inspector.commands.auto_balloon.get_active_document", lambda: document)
    monkeypatch.setattr(
        "assembly_inspector.commands.export_bom_csv.ask_save_file_path",
        lambda title, initial_path, file_filter: str(csv_path),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.export_bom_csv.show_info_message",
        lambda title, text: info_messages.append((title, text)),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.export_bom_csv.show_warning_message",
        lambda title, text: warning_messages.append((title, text)),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.auto_balloon.show_info_message",
        lambda title, text: info_messages.append((title, text)),
    )
    monkeypatch.setattr(
        "assembly_inspector.commands.auto_balloon.show_warning_message",
        lambda title, text: warning_messages.append((title, text)),
    )

    ExportBOMCsvCommand().Activated()
    AutoBalloonCommand().Activated()

    assert csv_path.exists()
    assert any("BOM exported to" in text for _, text in info_messages)
    assert any("Planned balloons" in text for _, text in info_messages)
    assert warning_messages == []

