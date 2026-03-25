"""GUI startup hook for FreeCAD Assembly Inspector."""

from assembly_inspector.workbench import AssemblyInspectorWorkbench

try:
    import FreeCADGui
except ImportError:  # pragma: no cover - only available inside FreeCAD
    FreeCADGui = None

if FreeCADGui is not None:
    FreeCADGui.addWorkbench(AssemblyInspectorWorkbench())

