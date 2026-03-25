"""Command registration for Assembly Inspector workbench."""

from __future__ import annotations

from collections import OrderedDict

from assembly_inspector.freecad_compat import Gui

from .auto_balloon import AutoBalloonCommand
from .export_bom_csv import ExportBOMCsvCommand
from .export_bom_xlsx import ExportBOMXlsxCommand
from .generate_bom import GenerateBOMCommand
from .scan_assembly import ScanAssemblyCommand
from .show_part_info import ShowPartInfoCommand

COMMANDS = OrderedDict(
    [
        ("AssemblyInspector_ScanAssembly", ScanAssemblyCommand),
        ("AssemblyInspector_ShowPartInfo", ShowPartInfoCommand),
        ("AssemblyInspector_GenerateBOM", GenerateBOMCommand),
        ("AssemblyInspector_ExportBOMCsv", ExportBOMCsvCommand),
        ("AssemblyInspector_ExportBOMXlsx", ExportBOMXlsxCommand),
        ("AssemblyInspector_AutoBalloon", AutoBalloonCommand),
    ]
)

WORKBENCH_COMMANDS = list(COMMANDS.keys())
_REGISTERED = False


def register_all_commands() -> None:
    """Register all commands exactly once."""
    global _REGISTERED
    if _REGISTERED or Gui is None:
        return
    for name, command_cls in COMMANDS.items():
        Gui.addCommand(name, command_cls())
    _REGISTERED = True
