"""BOM extraction and formatting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from assembly_inspector.models import PartRecord
from assembly_inspector.services.metadata_store import MetadataStore


@dataclass
class BOMRow:
    """One BOM row."""

    item_no: int
    part_id: str
    label: str
    quantity: int
    document_name: str
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        data = {
            "Item": str(self.item_no),
            "PartId": self.part_id,
            "Label": self.label,
            "Quantity": str(self.quantity),
            "Document": self.document_name,
        }
        data.update(self.metadata)
        return data


class BOMManager:
    """Generate BOM rows from part records and metadata."""

    def generate_rows(
        self,
        records: Iterable[PartRecord],
        metadata_store: MetadataStore | None = None,
    ) -> list[BOMRow]:
        grouped: dict[str, dict[str, object]] = {}

        for record in records:
            key = record.part_id or record.object_name
            item = grouped.setdefault(
                key,
                {
                    "record": record,
                    "quantity": 0,
                },
            )
            item["quantity"] = int(item["quantity"]) + max(1, int(record.quantity))

        rows: list[BOMRow] = []
        for idx, part_id in enumerate(sorted(grouped.keys()), start=1):
            group = grouped[part_id]
            record = group["record"]
            quantity = int(group["quantity"])
            metadata = metadata_store.get_metadata(part_id) if metadata_store else {}
            rows.append(
                BOMRow(
                    item_no=idx,
                    part_id=part_id,
                    label=record.label,
                    quantity=quantity,
                    document_name=record.document_name or "",
                    metadata=metadata,
                )
            )
        return rows

    @staticmethod
    def rows_to_text(rows: Iterable[BOMRow]) -> str:
        lines = ["Item\tPartId\tLabel\tQty\tDocument"]
        for row in rows:
            lines.append(
                f"{row.item_no}\t{row.part_id}\t{row.label}\t{row.quantity}\t{row.document_name}"
            )
        return "\n".join(lines)
