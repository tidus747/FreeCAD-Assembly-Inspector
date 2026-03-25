# FreeCAD-Assembly-Inspector

Minimal but extensible FreeCAD workbench for:
- assembly part identification
- spreadsheet-backed metadata inspection
- basic BOM generation
- future TechDraw auto-balloon workflows

## Status

This repository is an MVP+ architecture with working scan/info/BOM commands,
editable metadata persistence, BOM export, and best-effort TechDraw ballooning.
It is intentionally modular and conservative about unstable FreeCAD API
assumptions.

## Features in this MVP

- Workbench registration via `Init.py` and `InitGui.py`
- Commands:
  - `Scan Assembly`
  - `Show Part Info`
  - `Generate BOM`
  - `Export BOM CSV`
  - `Export BOM XLSX`
  - `Auto Balloon` (best-effort adapter-based)
- `PartRecord` model for normalized part registry entries
- `AssemblyScanner` service to collect relevant document objects
- `MetadataStore` abstraction
- Spreadsheet-backed adapter (`SpreadsheetAdapter` / `SpreadsheetMetadataStore`)
- Spreadsheet schema manager with migration marker + header validation
- `InMemoryMetadataStore` fallback with resilient wrapper
- `SelectionController` to react to selection changes
- Modeless editable metadata panel (validation + save)
- `BOMManager` for grouped BOM row extraction
- `BOMExporter` for CSV/XLSX exports and document spreadsheet persistence
- TechDraw adapter + collision-aware balloon planner
- Unit tests for pure logic and integration-like command activation

## Repository Layout

```text
FreeCAD-Assembly-Inspector/
|-- Init.py
|-- InitGui.py
|-- assembly_inspector/
|   |-- __init__.py
|   |-- freecad_compat.py
|   |-- logging_utils.py
|   |-- plugin_context.py
|   |-- workbench.py
|   |-- commands/
|   |   |-- __init__.py
|   |   |-- auto_balloon.py
|   |   |-- generate_bom.py
|   |   |-- scan_assembly.py
|   |   `-- show_part_info.py
|   |-- controllers/
|   |   |-- __init__.py
|   |   `-- selection_controller.py
|   |-- models/
|   |   |-- __init__.py
|   |   `-- part_record.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- auto_balloon_service.py
|   |   |-- assembly_scanner.py
|   |   |-- bom_exporter.py
|   |   |-- bom_manager.py
|   |   |-- metadata_store.py
|   |   |-- spreadsheet_adapter.py
|   |   |-- spreadsheet_schema.py
|   |   `-- techdraw_adapter.py
|   `-- ui/
|       |-- __init__.py
|       `-- info_panel.py
|-- tests/
|   |-- __init__.py
|   |-- conftest.py
|   |-- test_assembly_scanner.py
|   |-- test_auto_balloon.py
|   |-- test_bom_exporter.py
|   |-- test_bom_manager.py
|   |-- test_integration_commands.py
|   |-- test_metadata_store.py
|   `-- test_spreadsheet_schema.py
|-- LICENSE
|-- pyproject.toml
`-- README.md
```

## How It Works

1. User opens an assembly document.
2. `Scan Assembly` runs `AssemblyScanner` and builds a `PartRecord` registry.
3. `PluginContext` selects a metadata store:
   - Spreadsheet-backed when available.
   - In-memory fallback when spreadsheet APIs are unavailable/fail.
4. Spreadsheet schema is validated/migrated with a version marker.
5. Selection changes are observed by `SelectionController`.
6. Selected part metadata appears in an editable modeless panel and saves back to
   the active metadata store.
7. `Generate BOM` groups records by `part_id`, previews rows, and writes a BOM
   spreadsheet (`AssemblyInspectorBOM`) into the document.
8. Optional export commands write CSV/XLSX files.
9. `Auto Balloon` plans and attempts TechDraw callouts using adapter heuristics.

## Installation (Workbench-style)

1. Copy this repository into your FreeCAD `Mod` directory as:
   - `.../FreeCAD/Mod/FreeCAD-Assembly-Inspector`
2. Restart FreeCAD.
3. Activate the `Assembly Inspector` workbench.

## Running Tests

From repository root:

```powershell
python -m pytest -q
```

## Architecture Notes

- `freecad_compat.py` isolates runtime-only imports (`FreeCAD`, `FreeCADGui`, PySide).
- Pure logic modules (`services`, `models`) are test-friendly.
- Spreadsheet support is wrapped in adapter/store classes to contain API uncertainty.
- Spreadsheet schema/version handling is isolated in `spreadsheet_schema.py`.
- TechDraw integration is isolated in `techdraw_adapter.py` and `auto_balloon_service.py`.
- `plugin_context.py` centralizes state and command/service orchestration.

## Planned Next Steps

- Stable object identity strategy across linked/recomputed assemblies
- Configurable metadata schema templates and validation policies
- Improved TechDraw anchor extraction from geometry instead of view heuristics
- Rich BOM export panel (column mapping, filters, revisioning)
- Cross-version FreeCAD CI matrix with real integration smoke tests
