"""Metadata store abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from assembly_inspector.logging_utils import get_logger
from assembly_inspector.models import PartRecord

LOGGER = get_logger(__name__)


class MetadataStore(ABC):
    """Abstract metadata store interface keyed by part id."""

    @abstractmethod
    def get_metadata(self, part_id: str) -> dict[str, str]:
        """Return metadata for one part id."""

    @abstractmethod
    def set_metadata(self, part_id: str, metadata: dict[str, str]) -> None:
        """Persist metadata for one part id."""

    @abstractmethod
    def sync_with_records(self, records: Iterable[PartRecord]) -> None:
        """Ensure store has entries for discovered records."""

    @abstractmethod
    def list_part_ids(self) -> list[str]:
        """Return known part ids."""


class InMemoryMetadataStore(MetadataStore):
    """Simple in-memory metadata store used as default and fallback."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, str]] = {}

    def get_metadata(self, part_id: str) -> dict[str, str]:
        return dict(self._data.get(part_id, {}))

    def set_metadata(self, part_id: str, metadata: dict[str, str]) -> None:
        self._data[part_id] = {str(k): str(v) for k, v in metadata.items()}

    def sync_with_records(self, records: Iterable[PartRecord]) -> None:
        for record in records:
            self._data.setdefault(record.part_id, {})

    def list_part_ids(self) -> list[str]:
        return sorted(self._data.keys())


class FallbackMetadataStore(MetadataStore):
    """Try a primary store first and fall back to in-memory storage on failure."""

    def __init__(self, primary: MetadataStore, fallback: MetadataStore) -> None:
        self._primary = primary
        self._fallback = fallback

    def get_metadata(self, part_id: str) -> dict[str, str]:
        fallback_data = self._fallback.get_metadata(part_id)
        try:
            primary_data = self._primary.get_metadata(part_id)
        except Exception:
            LOGGER.exception("Primary metadata store failed on get; using fallback")
            return fallback_data

        merged = dict(fallback_data)
        merged.update(primary_data)
        return merged

    def set_metadata(self, part_id: str, metadata: dict[str, str]) -> None:
        self._fallback.set_metadata(part_id, metadata)
        try:
            self._primary.set_metadata(part_id, metadata)
        except Exception:
            LOGGER.exception("Primary metadata store failed on set; fallback retained")

    def sync_with_records(self, records: Iterable[PartRecord]) -> None:
        records = list(records)
        self._fallback.sync_with_records(records)
        try:
            self._primary.sync_with_records(records)
        except Exception:
            LOGGER.exception("Primary metadata store failed on sync; fallback retained")

    def list_part_ids(self) -> list[str]:
        ids = set(self._fallback.list_part_ids())
        try:
            ids.update(self._primary.list_part_ids())
        except Exception:
            LOGGER.exception("Primary metadata store failed on list; fallback retained")
        return sorted(ids)

