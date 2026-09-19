"""Deterministic local synthetic Solana populations for judge wiring."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.data.descriptors import DescriptorRegistration, EvidenceDescriptor, StoredDescriptor, descriptor_digest, load_descriptor_registry, register_descriptor
from gauntlet.ledger import Actor
from gauntlet.ledger._common import data_root_path

from .splits import SplitPolicy, _z


class SyntheticPopulationError(RuntimeError):
    """A machine-readable synthetic-population rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message); self.code = code; self.message = message; self.path = path


@dataclass(frozen=True, slots=True)
class BarRow:
    """One synthetic bar and its explicit temporal availability."""

    row_id: str; timestamp_utc: str; venue: str; token: str; open: int; high: int; low: int; close: int; volume: int
    feature_observed_at_utc: str; target_completed_at_utc: str

    def mapping(self) -> dict[str, object]:
        return {"row_id": self.row_id, "timestamp_utc": self.timestamp_utc, "venue": self.venue, "token": self.token, "open": self.open, "high": self.high, "low": self.low, "close": self.close, "volume": self.volume, "feature_observed_at_utc": self.feature_observed_at_utc, "target_completed_at_utc": self.target_completed_at_utc, "observation_basis": "MODELED", "evidence_class": "SYNTHETIC_FIXTURE"}


@dataclass(frozen=True, slots=True)
class EventRow:
    """One synthetic venue event used only for wiring provenance."""

    event_id: str; timestamp_utc: str; venue: str; token: str; event_type: str; amount: int

    def mapping(self) -> dict[str, object]:
        return {"event_id": self.event_id, "timestamp_utc": self.timestamp_utc, "venue": self.venue, "token": self.token, "event_type": self.event_type, "amount": self.amount, "observation_basis": "MODELED", "evidence_class": "SYNTHETIC_FIXTURE"}


@dataclass(frozen=True, slots=True)
class FrozenPopulation:
    """Registered synthetic fixture bytes, rows, and descriptor bindings."""

    seed: int; policy: SplitPolicy; bars: tuple[BarRow, ...]; events: tuple[EventRow, ...]
    bars_descriptor: Mapping[str, object]; events_descriptor: Mapping[str, object]
    bars_content_path: Path; events_content_path: Path; bars_content_hash: str; events_content_hash: str; population_hash: str

    def digest(self) -> str:
        value = {"bars": [row.mapping() for row in self.bars], "bars_descriptor_hash": self.bars_descriptor["descriptor_hash"], "bars_content_hash": self.bars_content_hash, "events": [row.mapping() for row in self.events], "events_descriptor_hash": self.events_descriptor["descriptor_hash"], "events_content_hash": self.events_content_hash, "policy_hash": self.policy.hash, "seed": self.seed}
        return sha256_digest(canonical_json(value))

    def mapping(self) -> dict[str, object]:
        return {"schema_version": "gauntlet.synthetic-population.v1", "seed": self.seed, "policy": self.policy.mapping(), "population_hash": self.population_hash, "promotable_venue_evidence": False, "evidence_class": "SYNTHETIC_FIXTURE", "bars": [row.mapping() for row in self.bars], "events": [row.mapping() for row in self.events], "bars_descriptor": dict(self.bars_descriptor), "events_descriptor": dict(self.events_descriptor)}


@dataclass(frozen=True, slots=True)
class _DescriptorBinding:
    stored: StoredDescriptor; content_path: Path


def _timestamp(policy: SplitPolicy, index: int) -> str:
    return _z(policy.start_at + timedelta(seconds=index * policy.bar_interval_seconds))


def _required_bars(policy: SplitPolicy) -> int:
    gap = policy.embargo_bars + policy.purge_bars
    cursor = 0
    for index in range(policy.fold_count):
        train_end = cursor + policy.train_bars + policy.target_horizon_bars if index == 0 or not policy.expanding_window else cursor
        cursor = train_end + gap + policy.validation_bars + policy.target_horizon_bars + gap + policy.test_bars + policy.target_horizon_bars
    return cursor + policy.target_horizon_bars + 2


def _rows(seed: int, policy: SplitPolicy) -> tuple[tuple[BarRow, ...], tuple[EventRow, ...]]:
    generator = random.Random(f"{seed}:{policy.hash}")
    tokens = ("SOL", "JUP", "USDC")
    bars: list[BarRow] = []
    events: list[EventRow] = []
    for index in range(_required_bars(policy)):
        timestamp = _timestamp(policy, index)
        token = tokens[index % len(tokens)]
        open_price = 100 + generator.randrange(0, 50)
        close_price = max(1, open_price + generator.randrange(-12, 13))
        bars.append(BarRow(f"bar-{index:06d}", timestamp, "solana_dex", token, open_price, max(open_price, close_price) + generator.randrange(0, 4), max(1, min(open_price, close_price) - generator.randrange(0, 4)), close_price, generator.randrange(100, 10_000), timestamp, _timestamp(policy, index + policy.target_horizon_bars)))
        if index % 3 == 0:
            events.append(EventRow(f"event-{index:06d}", timestamp, "solana_dex", token, "swap" if index % 6 else "liquidity", generator.randrange(1, 5000)))
    return tuple(bars), tuple(events)


def _content(kind: str, seed: int, policy: SplitPolicy, rows: tuple[dict[str, object], ...]) -> bytes:
    return canonical_json({"schema_version": "gauntlet.synthetic-population.v1", "kind": kind, "evidence_class": "SYNTHETIC_FIXTURE", "promotable_venue_evidence": False, "seed": seed, "policy_hash": policy.hash, "rows": rows})


def _descriptor(kind: str, seed: int, policy: SplitPolicy, content: bytes, dependencies: tuple[dict[str, str], ...]) -> EvidenceDescriptor:
    artifact_id = f"solana.{kind}.synthetic.{seed}.{policy.hash[7:19]}"
    unsealed = EvidenceDescriptor(
        descriptor_schema="gauntlet.evidence.v1", artifact_id=artifact_id, descriptor_id=f"{artifact_id}.descriptor", descriptor_version=1,
        descriptor_hash=sha256_digest(b""), supersedes_descriptor_hash=None, effective_at_utc=_z(policy.start_at), superseded_at_utc=None,
        kind=kind, venue_track="solana_dex", content_hash=sha256_digest(content), source={"collector": "synthetic-generator", "uri_or_lineage": f"gauntlet://synthetic/{kind}/{seed}/{policy.hash}"},
        observation_basis="MODELED", coverage={"start_utc": _z(policy.start_at), "end_exclusive_utc": _timestamp(policy, _required_bars(policy))},
        freshness={"watermark_at": _timestamp(policy, _required_bars(policy)), "max_age": "P3650D"}, quality={"state": "VALID", "checks": [{"name": "deterministic-local-generation", "status": "PASS"}]},
        dependencies=dependencies, criticality="GATE_CRITICAL", downstream_metrics=("judge.walk_forward.synthetic_wiring",), content_bytes=content, actor=Actor("collector", "synthetic-generator"),
    )
    return replace(unsealed, descriptor_hash=descriptor_digest(unsealed))


def _bind(descriptor: EvidenceDescriptor) -> _DescriptorBinding:
    records = load_descriptor_registry(data_root_path(None))
    existing = records.get(descriptor.descriptor_hash)
    if existing is not None: return _DescriptorBinding(existing, existing.content_path)
    return _DescriptorBinding(_stored(register_descriptor(descriptor)), (data_root_path(None) / "artifacts" / f"{descriptor.content_hash}.bin"))


def _stored(registration: DescriptorRegistration) -> StoredDescriptor:
    records = load_descriptor_registry(data_root_path(None))
    stored = records.get(registration.descriptor_hash)
    if stored is None: raise SyntheticPopulationError("REGISTRATION_UNVERIFIED", "registered descriptor cannot be reloaded")
    return stored


def build_synthetic_population(seed: int, policy: SplitPolicy) -> FrozenPopulation:
    """Generate and register a deterministic local bars/events fixture population."""

    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0: raise SyntheticPopulationError("SEED_INVALID", "seed must be a non-negative integer", "$.seed")
    bars, events = _rows(seed, policy)
    bars_content = _content("bars", seed, policy, [row.mapping() for row in bars])
    events_content = _content("events", seed, policy, [row.mapping() for row in events])
    bars_descriptor = _descriptor("bars", seed, policy, bars_content, ())
    bars_binding = _bind(bars_descriptor)
    events_descriptor = _descriptor("events", seed, policy, events_content, ({"artifact_id": bars_descriptor.artifact_id, "relation": "requires"},))
    events_binding = _bind(events_descriptor)
    population = FrozenPopulation(seed, policy, bars, events, MappingProxyType(bars_binding.stored.value), MappingProxyType(events_binding.stored.value), bars_binding.content_path, events_binding.content_path, sha256_digest(bars_content), sha256_digest(events_content), "")
    object.__setattr__(population, "population_hash", population.digest())
    return population


__all__ = ["BarRow", "EventRow", "FrozenPopulation", "SyntheticPopulationError", "build_synthetic_population"]
