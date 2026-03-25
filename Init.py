"""FreeCAD Assembly Inspector startup hook.

This module is imported by FreeCAD when the addon is discovered.
"""

from assembly_inspector.logging_utils import configure_logging

configure_logging()

