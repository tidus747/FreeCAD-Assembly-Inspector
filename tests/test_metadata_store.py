"""Tests for metadata stores."""

from assembly_inspector.models import PartRecord
from assembly_inspector.services.metadata_store import (
    FallbackMetadataStore,
    InMemoryMetadataStore,
    MetadataStore,
)


class FailingStore(MetadataStore):
    """Primary store test double that always fails."""

    def get_metadata(self, part_id: str) -> dict[str, str]:
        raise RuntimeError("not available")

    def set_metadata(self, part_id: str, metadata: dict[str, str]) -> None:
        raise RuntimeError("not available")

    def sync_with_records(self, records):
        raise RuntimeError("not available")

    def list_part_ids(self) -> list[str]:
        raise RuntimeError("not available")


def test_in_memory_metadata_store_sync_and_get_set():
    store = InMemoryMetadataStore()
    record = PartRecord(part_id="PN-001", object_name="Obj001", label="Obj 001")

    store.sync_with_records([record])
    assert store.get_metadata("PN-001") == {}

    store.set_metadata("PN-001", {"Description": "Bracket"})
    assert store.get_metadata("PN-001") == {"Description": "Bracket"}


def test_fallback_metadata_store_uses_secondary_store_on_errors():
    fallback = InMemoryMetadataStore()
    store = FallbackMetadataStore(primary=FailingStore(), fallback=fallback)

    record = PartRecord(part_id="PN-002", object_name="Obj002", label="Obj 002")
    store.sync_with_records([record])
    store.set_metadata("PN-002", {"Material": "Aluminum"})

    assert store.get_metadata("PN-002") == {"Material": "Aluminum"}
    assert "PN-002" in store.list_part_ids()

