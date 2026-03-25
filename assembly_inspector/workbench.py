"""FreeCAD workbench registration."""

from __future__ import annotations

from assembly_inspector.commands import WORKBENCH_COMMANDS, register_all_commands
from assembly_inspector.freecad_compat import Gui
from assembly_inspector.plugin_context import get_context
from assembly_inspector.resources import get_icon_path


if Gui is not None:  # pragma: no cover - loaded only in FreeCAD GUI

    class AssemblyInspectorWorkbench(Gui.Workbench):
        """Assembly Inspector workbench."""

        MenuText = "Assembly Inspector"
        ToolTip = "Inspect assembly parts, metadata, and BOM data."
        Icon = get_icon_path("scan_assembly.svg")

        def Initialize(self) -> None:  # noqa: N802
            register_all_commands()
            self.appendToolbar("Assembly Inspector", WORKBENCH_COMMANDS)
            self.appendMenu("Assembly Inspector", WORKBENCH_COMMANDS)
            get_context().initialize()

        def Activated(self) -> None:  # noqa: N802
            get_context().attach_selection_observer()

        def Deactivated(self) -> None:  # noqa: N802
            get_context().detach_selection_observer()

        def GetClassName(self) -> str:  # noqa: N802
            return "Gui::PythonWorkbench"

else:

    class AssemblyInspectorWorkbench:  # pragma: no cover - fallback for tests
        """Non-FreeCAD fallback workbench class."""

        pass
