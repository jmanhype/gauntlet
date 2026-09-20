"""Canonical import and validation of the QTS portfolio-risk policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from gauntlet.contracts.canonical import CanonicalJSONError, canonical_json, sha256_digest
from gauntlet.contracts.schemas import POLICY, validate
from gauntlet.ledger import Actor
from gauntlet.ledger._common import LedgerError, actor_mapping, validate_digest, validate_timestamp


RISK_POLICY_ID = "qts.risk"
RISK_POLICY_VERSION = 1
RISK_POLICY_PATH = Path(__file__).resolve().parents[3] / "policies" / "risk" / "qts.risk@v1.json"


class RiskError(RuntimeError):
    """A machine-readable, fail-closed risk-policy rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


@dataclass(frozen=True, slots=True)
class QTSSource:
    """The exact external QTS bytes selected for import."""

    source_path: Path
    source_repository: str
    source_file: str
    source_content_hash: str
    imported_at_utc: str


@dataclass(frozen=True, slots=True)
class OwnerAuthorizationRef:
    """A non-secret reference to the owner's recorded authorization."""

    actor: Actor
    authorization_id: str
    authorization_hash: str
    authorized_at_utc: str


@dataclass(frozen=True, slots=True)
class RiskPolicyVersion:
    """A sealed policy version and its exact canonical projection."""

    policy_id: str
    version: int
    status: str
    policy_hash: str
    canonical_bytes: bytes
    payload: Mapping[str, object]
    path: Path

    @property
    def rules(self) -> Mapping[str, object]:
        value = self.payload.get("rules")
        if not isinstance(value, Mapping):
            raise RiskError("POLICY_INVALID", "rules must be an object", "$.rules")
        return value

    @property
    def trial_history_input(self) -> dict[str, object]:
        """Values whose change requires a new research trial."""

        return {
            "policy_id": self.policy_id,
            "policy_version": self.version,
            "policy_hash": self.policy_hash,
            "requires_new_trial_on_change": True,
            "changed_fields": [
                "max_position_size", "per_trade_risk_percent", "max_leverage",
                "position_sizing.concentration_limit_percent", "max_drawdown_percent",
                "circuit_breakers.daily_loss_usd", "circuit_breakers.drawdown_percent",
                "emergency_procedures.position_reduction_factor",
            ],
        }


def _invalid(message: str, path: str = "$", code: str = "POLICY_INVALID") -> RiskError:
    return RiskError(code, message, path)


def _timestamp(value: object, path: str) -> None:
    try:
        validate_timestamp(value, path)
    except LedgerError as error:
        raise _invalid(error.message, error.path or path) from error


def _digest(value: object, path: str) -> str:
    try:
        validate_digest(value, path)
    except LedgerError as error:
        raise _invalid(error.message, error.path or path) from error
    assert isinstance(value, str)
    return value


def _leaves(value: object, prefix: str = "") -> set[str]:
    if isinstance(value, Mapping):
        result: set[str] = set()
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            result.update(_leaves(item, child))
        return result
    return {prefix}


def _policy_object(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise _invalid("risk policy must be a regular non-symlink file", str(path), "POLICY_READ_FAILED")
    try:
        value: object = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _invalid(f"risk policy cannot be read: {error}", str(path), "POLICY_READ_FAILED") from error
    if not isinstance(value, dict):
        raise _invalid("risk policy must be a JSON object", str(path), "POLICY_READ_FAILED")
    return value


def seal_risk_policy(value: Mapping[str, object], path: Path = RISK_POLICY_PATH) -> RiskPolicyVersion:
    """Validate and seal a policy mapping without accepting secret material."""

    if not isinstance(value, Mapping):
        raise _invalid("risk policy must be an object")
    unsigned = dict(value)
    declared = unsigned.pop("content_hash", None)
    expected = sha256_digest(canonical_json(unsigned))
    actual = _digest(declared, "content_hash")
    if actual != expected:
        raise _invalid("content_hash does not match the canonical unsigned policy", "$.content_hash", "POLICY_HASH_MISMATCH")
    result = validate(unsigned | {"content_hash": actual}, POLICY)
    if not result.valid:
        first = result.errors[0]
        raise _invalid(first.message, first.path, "POLICY_SCHEMA_INVALID")
    rules = unsigned.get("rules")
    if not isinstance(rules, Mapping) or not isinstance(rules.get("source"), Mapping):
        raise _invalid("rules.source must be an object", "$.rules.source")
    for section in ("units", "scopes", "semantics", "venue_applicability", "domain_separation"):
        if not isinstance(rules.get(section), Mapping):
            raise _invalid(f"rules.{section} must be an object", f"$.rules.{section}")
    source_fields = _leaves(rules["source"])
    for section in ("units", "scopes", "semantics"):
        fields = set(rules[section])  # type: ignore[arg-type]
        missing = sorted(source_fields - fields)
        if missing:
            raise _invalid(f"QTS field(s) lack {section}: {missing}", f"$.rules.{section}", "POLICY_LINEAGE_INCOMPLETE")
    lineage = unsigned.get("lineage")
    if not isinstance(lineage, Mapping):
        raise _invalid("lineage must be an object", "$.lineage")
    source_lineage = lineage.get("source")
    authorization = lineage.get("authorization")
    if not isinstance(source_lineage, Mapping) or not isinstance(authorization, Mapping):
        raise _invalid("source and authorization lineage are required", "$.lineage")
    _digest(source_lineage.get("content_hash"), "lineage.source.content_hash")
    _digest(authorization.get("authorization_hash"), "lineage.authorization.authorization_hash")
    _timestamp(lineage.get("imported_at_utc"), "$.lineage.imported_at_utc")
    _timestamp(authorization.get("authorized_at_utc"), "$.lineage.authorization.authorized_at_utc")
    try:
        canonical = canonical_json(unsigned | {"content_hash": actual})
    except CanonicalJSONError as error:
        raise _invalid(error.message, error.path) from error
    return RiskPolicyVersion(
        policy_id=str(unsigned["policy_id"]),
        version=int(unsigned["version"]),  # type: ignore[arg-type]
        status=str(unsigned["status"]),
        policy_hash=actual,
        canonical_bytes=canonical,
        payload=MappingProxyType(unsigned | {"content_hash": actual}),
        path=Path(path),
    )


def load_risk_policy(path: Path = RISK_POLICY_PATH) -> RiskPolicyVersion:
    """Load and verify the canonical tracked policy file."""

    policy = seal_risk_policy(_policy_object(Path(path)), Path(path))
    if policy.policy_id != RISK_POLICY_ID or policy.version != RISK_POLICY_VERSION:
        raise _invalid("unexpected risk policy identity or version", "$.policy_id")
    return policy


def import_qts(source: QTSSource, authorization: OwnerAuthorizationRef) -> RiskPolicyVersion:
    """Bind exact QTS bytes, complete lineage, and owner authorization."""

    if not isinstance(source, QTSSource) or not isinstance(authorization, OwnerAuthorizationRef):
        raise _invalid("source and authorization must use their typed contracts")
    if not source.source_repository.strip() or not source.source_file.strip():
        raise _invalid("source repository and file are required", "$.source")
    _timestamp(source.imported_at_utc, "$.source.imported_at_utc")
    expected_source_hash = _digest(source.source_content_hash, "$.source.source_content_hash")
    _digest(authorization.authorization_hash, "$.authorization.authorization_hash")
    _timestamp(authorization.authorized_at_utc, "$.authorization.authorized_at_utc")
    if not authorization.authorization_id.strip():
        raise _invalid("authorization_id must be non-empty", "$.authorization.authorization_id")
    actor_mapping(authorization.actor)

    path = Path(source.source_path)
    if path.is_symlink() or not path.is_file():
        raise _invalid("QTS source must be a regular non-symlink file", str(path), "SOURCE_READ_FAILED")
    try:
        source_bytes = path.read_bytes()
        source_value: object = json.loads(source_bytes)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _invalid(f"QTS source cannot be read: {error}", str(path), "SOURCE_READ_FAILED") from error
    if not isinstance(source_value, dict):
        raise _invalid("QTS source must be a JSON object", str(path), "SOURCE_READ_FAILED")
    actual_source_hash = sha256_digest(source_bytes)
    if actual_source_hash != expected_source_hash:
        raise _invalid("QTS source bytes do not match source_content_hash", "$.source.source_content_hash", "SOURCE_HASH_MISMATCH")

    policy = load_risk_policy()
    lineage = policy.payload.get("lineage")
    rules = policy.rules
    source_section = rules.get("source")
    assert isinstance(lineage, Mapping) and isinstance(source_section, Mapping)
    source_lineage = lineage.get("source")
    policy_authorization = lineage.get("authorization")
    assert isinstance(source_lineage, Mapping) and isinstance(policy_authorization, Mapping)
    if source_lineage.get("content_hash") != actual_source_hash:
        raise _invalid("policy lineage does not bind the exact QTS bytes", "$.lineage.source.content_hash", "POLICY_LINEAGE_MISMATCH")
    if canonical_json(source_value) != canonical_json(source_section):
        raise _invalid("policy rules differ from exact QTS source values", "$.rules.source", "POLICY_SOURCE_MISMATCH")
    if source_lineage.get("repository") != source.source_repository or source_lineage.get("file") != source.source_file:
        raise _invalid("policy source repository/file mismatch", "$.lineage.source", "POLICY_LINEAGE_MISMATCH")
    if lineage.get("imported_at_utc") != source.imported_at_utc or policy_authorization.get("kind") != authorization.actor.kind or policy_authorization.get("identity") != authorization.actor.identity:
        raise _invalid("QTS import time or owner actor does not match policy lineage", "$.lineage", "POLICY_LINEAGE_MISMATCH")
    if policy_authorization.get("authorization_id") != authorization.authorization_id or policy_authorization.get("authorization_hash") != authorization.authorization_hash:
        raise _invalid("owner authorization reference does not match policy lineage", "$.lineage.authorization", "AUTHORIZATION_MISMATCH")
    if policy_authorization.get("authorized_at_utc") != authorization.authorized_at_utc:
        raise _invalid("owner authorization time does not match policy lineage", "$.lineage.authorization.authorized_at_utc", "AUTHORIZATION_MISMATCH")
    return policy


__all__ = [
    "OwnerAuthorizationRef", "RISK_POLICY_ID", "RISK_POLICY_PATH", "RISK_POLICY_VERSION",
    "QTSSource", "RiskError", "RiskPolicyVersion", "import_qts", "load_risk_policy", "seal_risk_policy",
]
