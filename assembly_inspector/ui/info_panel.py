"""Part information dialog."""

from __future__ import annotations

from typing import Any, Callable

from assembly_inspector.models import PartRecord

try:  # pragma: no cover - runtime dependent
    from PySide2 import QtCore, QtWidgets
except ImportError:  # pragma: no cover
    try:
        from PySide import QtCore  # type: ignore
        from PySide import QtGui as QtWidgets  # type: ignore
    except ImportError:
        QtCore = None
        QtWidgets = None


class PartInfoDialog(QtWidgets.QDialog if QtWidgets is not None else object):
    """Modeless dialog for part metadata inspection and editing."""

    def __init__(self, parent: Any = None) -> None:
        if QtWidgets is None:  # pragma: no cover
            return
        super().__init__(parent)
        self.setWindowTitle("Assembly Inspector - Part Metadata")
        self.setModal(False)
        self.resize(520, 420)
        self._on_save: Callable[[str, dict[str, str]], None] | None = None
        self._current_part_id = ""

        layout = QtWidgets.QVBoxLayout(self)

        group = QtWidgets.QGroupBox("Part")
        form = QtWidgets.QFormLayout(group)
        self._label_part_id = QtWidgets.QLabel("")
        self._label_name = QtWidgets.QLabel("")
        self._label_object = QtWidgets.QLabel("")
        self._label_type = QtWidgets.QLabel("")
        self._label_document = QtWidgets.QLabel("")
        form.addRow("Part ID", self._label_part_id)
        form.addRow("Label", self._label_name)
        form.addRow("Object", self._label_object)
        form.addRow("Type", self._label_type)
        form.addRow("Document", self._label_document)
        layout.addWidget(group)

        layout.addWidget(QtWidgets.QLabel("Metadata"))
        self._table = QtWidgets.QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Key", "Value"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(
            QtWidgets.QAbstractItemView.DoubleClicked
            | QtWidgets.QAbstractItemView.EditKeyPressed
            | QtWidgets.QAbstractItemView.SelectedClicked
        )
        layout.addWidget(self._table, stretch=1)

        button_row = QtWidgets.QHBoxLayout()
        self._btn_add = QtWidgets.QPushButton("Add Row")
        self._btn_remove = QtWidgets.QPushButton("Remove Row")
        self._btn_save = QtWidgets.QPushButton("Save Metadata")
        button_row.addWidget(self._btn_add)
        button_row.addWidget(self._btn_remove)
        button_row.addStretch(1)
        button_row.addWidget(self._btn_save)
        layout.addLayout(button_row)

        self._btn_add.clicked.connect(self._add_row)
        self._btn_remove.clicked.connect(self._remove_selected_row)
        self._btn_save.clicked.connect(self._save_metadata)

    def set_on_save(self, callback: Callable[[str, dict[str, str]], None] | None) -> None:
        """Set callback fired on metadata save."""
        self._on_save = callback

    def set_part_data(self, record: PartRecord, metadata: dict[str, str]) -> None:
        """Populate the dialog with one part record and its metadata."""
        if QtWidgets is None:  # pragma: no cover
            return

        self._current_part_id = record.part_id
        self._label_part_id.setText(record.part_id)
        self._label_name.setText(record.label)
        self._label_object.setText(record.object_name)
        self._label_type.setText(record.type_id or "")
        self._label_document.setText(record.document_name or "")

        rows = sorted(metadata.items())
        self._table.setRowCount(len(rows))
        for idx, (key, value) in enumerate(rows):
            self._table.setItem(idx, 0, QtWidgets.QTableWidgetItem(str(key)))
            self._table.setItem(idx, 1, QtWidgets.QTableWidgetItem(str(value)))

    def _add_row(self) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        self._table.setItem(row, 1, QtWidgets.QTableWidgetItem(""))
        self._table.setCurrentCell(row, 0)
        self._table.editItem(self._table.item(row, 0))

    def _remove_selected_row(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)

    def _save_metadata(self) -> None:
        metadata: dict[str, str] = {}
        for row in range(self._table.rowCount()):
            key_item = self._table.item(row, 0)
            val_item = self._table.item(row, 1)
            key = (key_item.text() if key_item else "").strip()
            value = (val_item.text() if val_item else "").strip()

            if not key and not value:
                continue
            if not key:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Assembly Inspector",
                    "Metadata key cannot be empty.",
                )
                return
            if key in metadata:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Assembly Inspector",
                    f"Duplicated metadata key: '{key}'",
                )
                return
            metadata[key] = value

        if self._on_save and self._current_part_id:
            self._on_save(self._current_part_id, metadata)
            QtWidgets.QMessageBox.information(self, "Assembly Inspector", "Metadata saved.")


def update_or_create_dialog(
    record: PartRecord,
    metadata: dict[str, str],
    dialog: PartInfoDialog | None = None,
    parent: Any = None,
    on_save: Callable[[str, dict[str, str]], None] | None = None,
) -> PartInfoDialog | None:
    """Create or update a modeless part metadata dialog."""
    if QtWidgets is None:
        return None

    panel = dialog or PartInfoDialog(parent=parent)
    panel.set_on_save(on_save)
    panel.set_part_data(record, metadata)
    panel.show()
    panel.raise_()
    panel.activateWindow()
    return panel
