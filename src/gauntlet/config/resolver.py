"""Complete, immutable, fail-closed run-configuration resolution."""

from __future__ import annotations

import math, tomllib
from dataclasses import asdict, dataclass
from datetime import date; from pathlib import Path; from types import MappingProxyType; from typing import Mapping

from gauntlet.contracts.canonical import CanonicalJSONError, canonical_json, sha256_digest


CONFIG_SCHEMA = "gauntlet.resolved-config.v1"
DEFAULTS_VERSION = "gauntlet.defaults@v1"
REDACTION_RULE_VERSION = "gauntlet.redaction@v1"
_RESOLVER_VERSION = "1"
_VENUES = frozenset(("solana_dex", "hyperliquid", "external", "cross_venue_transfer"))
_REQUIRED_FIELDS = ("venue_track", "data_start", "data_end", "seed", "lookback", "horizon", "threshold", "fee_bps")
_OPTIONAL_FIELDS = ("runtime_secret_name",)
_PROFILE_FIELDS = frozenset({"schema_version", "profile_id", "profile_version", "values", *_OPTIONAL_FIELDS})
_SECRET_PARTS = ("password", "secret", "credential", "private", "token", "key")


@dataclass(frozen=True)
class ArtifactVersions:
    """Every material schema, policy, evidence, data, model, and code version."""

    schema_version: str; policy_version: str; evidence_version: str; data_version: str; model_version: str
    code_version: str; dependency_lock_hash: str; environment_hash: str

    def mapping(self) -> dict[str, object]: return dict(asdict(self))


@dataclass(frozen=True)
class ResolvedConfig:
    """A sealed complete configuration artifact and its exact canonical bytes."""

    schema_version: str; profile_hash: str; config_hash: str; canonical_bytes: bytes; artifact: Mapping[str, object]


class ConfigError(RuntimeError):
    """A machine-readable, mutation-free configuration rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message); self.code = code; self.message = message; self.path = path


def _invalid(message: str, path: str = "$") -> ConfigError:
    return ConfigError("CONFIG_INVALID", message, path)


def _redacted(kind: str) -> dict[str, object]:
    return {"redacted": True, "rule_version": REDACTION_RULE_VERSION, "kind": kind}


def _freeze(value: object) -> object:
    if isinstance(value, Mapping): return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)): return tuple(_freeze(item) for item in value)
    return value


def _nonempty(value: object, path: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise _invalid("must be a non-empty string", path)
    return value


def _is_digest(value: str) -> bool:
    hexadecimal = value[7:]
    return value.startswith("sha256:") and len(hexadecimal) == 64 and all(char in "0123456789abcdef" for char in hexadecimal)


def _validate_versions(value: ArtifactVersions) -> dict[str, object]:
    result = value.mapping()
    for field, item in result.items():
        path = f"$.artifact_versions.{field}"
        if not isinstance(item, str) or not item.strip(): raise _invalid("must be a non-empty string", path)
        if field.endswith("_hash") and not _is_digest(item): raise _invalid("must be sha256:<64 lowercase hexadecimal>", path)
    return result


def _secret_key(key: str) -> bool:
    normalized = key.casefold().replace("-", "_").replace(" ", "_")
    return any(part in normalized for part in _SECRET_PARTS)


def _reject_secrets(value: object, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str): raise _invalid("object keys must be strings", path)
            if _secret_key(key) and key != "runtime_secret_name": raise _invalid("secret material is never accepted", f"{path}.{key}")
            _reject_secrets(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value): _reject_secrets(item, f"{path}[{index}]")
    elif isinstance(value, str) and ((value.startswith("sk-") and len(value) >= 20) or ("BEGIN PRIVATE KEY" in value.upper())):
        raise _invalid("possible API-key material is never accepted", path)


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1: raise _invalid("must be a positive integer", f"$.values.{field}")
    return value


def _validate_values(values: Mapping[str, object]) -> dict[str, object]:
    unknown = sorted(set(values) - {*_REQUIRED_FIELDS, *_OPTIONAL_FIELDS})
    if unknown: raise _invalid(f"unregistered field(s): {unknown}", "$.values")
    missing = sorted(field for field in _REQUIRED_FIELDS if field not in values)
    if missing: raise _invalid(f"research-critical field(s) are incomplete: {missing}", "$.values")
    checked: dict[str, object] = dict(values)
    for field in ("seed", "lookback", "horizon"): checked[field] = _positive_int(values[field], field)
    venue = values["venue_track"]
    if not isinstance(venue, str): raise _invalid("must be a string", "$.values.venue_track")
    if venue not in _VENUES: raise _invalid(f"must be one of {sorted(_VENUES)}", "$.values.venue_track")
    for field in ("data_start", "data_end"):
        try:
            date.fromisoformat(values[field])  # type: ignore[arg-type]
        except (TypeError, ValueError) as error:
            raise _invalid("must be an ISO-8601 date", f"$.values.{field}") from error
    if date.fromisoformat(str(values["data_end"])) <= date.fromisoformat(str(values["data_start"])):
        raise _invalid("data_end must be after data_start", "$.values.data_end")
    threshold = values["threshold"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise _invalid("must be a finite number between zero and one", "$.values.threshold")
    fees = values["fee_bps"]
    if isinstance(fees, bool) or not isinstance(fees, (int, float)) or not math.isfinite(fees) or fees < 0:
        raise _invalid("must be a finite non-negative number", "$.values.fee_bps")
    if "runtime_secret_name" in checked:
        checked["runtime_secret_name"] = _nonempty(checked["runtime_secret_name"], "$.values.runtime_secret_name")
    return checked


def _profile(path: Path) -> tuple[dict[str, object], str]:
    if path.is_symlink() or not path.is_file():
        raise _invalid("profile must be a regular non-symlink file", str(path))
    try: content = path.read_bytes()
    except OSError as error: raise _invalid(f"profile cannot be read: {error}", str(path)) from error
    try:
        value: object = tomllib.loads(content.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise _invalid(f"profile cannot be read as UTF-8 TOML: {error}", str(path)) from error
    if not isinstance(value, dict):
        raise _invalid("profile must contain a TOML object", str(path))
    unknown = sorted(set(value) - _PROFILE_FIELDS)
    missing = sorted(_PROFILE_FIELDS - set(value) - set(_OPTIONAL_FIELDS))
    if unknown or missing:
        raise _invalid(f"unknown fields: {unknown}" if unknown else f"missing fields: {missing}", "$")
    if value["schema_version"] != "1":
        raise _invalid("profile schema_version must be '1'", "$.schema_version")
    _nonempty(value["profile_id"], "$.profile_id")
    version = value["profile_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1: raise _invalid("must be a positive integer", "$.profile_version")
    if not isinstance(value["values"], dict): raise _invalid("must be an object", "$.values")
    return value, sha256_digest(content)


def resolve_config(profile: Path, overrides: Mapping[str, object], artifact_versions: ArtifactVersions) -> ResolvedConfig:
    """Resolve and seal defaults, a real profile, explicit overrides, and versions."""

    if not isinstance(overrides, Mapping): raise _invalid("overrides must be an object", "$.overrides")
    if any(not isinstance(key, str) for key in overrides): raise _invalid("override keys must be strings", "$.overrides")
    if not isinstance(artifact_versions, ArtifactVersions): raise _invalid("artifact_versions has the wrong type", "$.artifact_versions")
    _reject_secrets(overrides, "$.overrides")
    _reject_secrets(artifact_versions.mapping(), "$.artifact_versions")
    versions = _validate_versions(artifact_versions)
    document, profile_hash = _profile(Path(profile))
    _reject_secrets(document, "$")
    profile_values = dict(document["values"])  # type: ignore[arg-type]
    profile_values = _validate_values(profile_values)
    unknown_overrides = sorted(set(overrides) - set(_REQUIRED_FIELDS))
    if unknown_overrides: raise _invalid(f"unregistered override field(s): {unknown_overrides}", f"$.overrides.{unknown_overrides[0]}")
    checked_overrides = _validate_values({**profile_values, **overrides})
    explicit = {key: checked_overrides[key] for key in overrides}

    effective = {**profile_values, **explicit}
    redacted_fields = ["runtime.data_root"]
    if "runtime_secret_name" in effective:
        effective["runtime.secret_name"] = _redacted("secret_name")
        del effective["runtime_secret_name"]
        redacted_fields.append("runtime.secret_name")
    effective["runtime.data_root"] = _redacted("runtime_path")
    effective["runtime.mode"] = "local-single-owner"
    provenance: dict[str, dict[str, str]] = {}
    for field in effective:
        if field in explicit:
            provenance[field] = {"source": "override", "value": "explicit"}
        elif field in profile_values or field == "runtime.secret_name":
            provenance[field] = {"source": "profile", "id": str(document["profile_id"]), "version": str(document["profile_version"])}
        else:
            provenance[field] = {"source": "defaults", "version": DEFAULTS_VERSION}
    artifact: dict[str, object] = {
        "schema_version": CONFIG_SCHEMA,
        "resolver_version": _RESOLVER_VERSION,
        "defaults": {"version": DEFAULTS_VERSION, "values": {"runtime.mode": "local-single-owner", "runtime.data_root": _redacted("runtime_path")}},
        "profile": {"id": document["profile_id"], "version": document["profile_version"], "content_hash": profile_hash},
        "overrides": explicit,
        "values": dict(sorted(effective.items())),
        "artifact_versions": versions,
        "provenance": dict(sorted(provenance.items())),
        "redaction_rule": {"version": REDACTION_RULE_VERSION, "redacted_fields": sorted(redacted_fields)},
    }
    try:
        canonical = canonical_json(artifact)
    except CanonicalJSONError as error:
        raise _invalid(f"resolved configuration is not canonical JSON: {error.message}", error.path) from error
    return ResolvedConfig(CONFIG_SCHEMA, profile_hash, sha256_digest(canonical), canonical, MappingProxyType(_freeze(artifact)))  # type: ignore[arg-type]


__all__ = ["DEFAULTS_VERSION", "REDACTION_RULE_VERSION", "ArtifactVersions", "ConfigError", "ResolvedConfig", "resolve_config"]
