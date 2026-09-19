"""Provenance-preserving comparison of resolved configurations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .resolver import ResolvedConfig


_THRESHOLD_FIELDS = frozenset(("venue_track", "data_start", "data_end", "seed", "lookback", "horizon", "threshold", "fee_bps"))


@dataclass(frozen=True)
class ConfigProvenance:
    """The visible origin and immutable identity behind one config leaf."""

    source: str; value: str | None = None; identifier: str | None = None
    version: str | None = None; content_hash: str | None = None


@dataclass(frozen=True)
class ConfigValue:
    """One effective leaf and the provenance that produced it."""

    key: str; value: object; provenance: ConfigProvenance


@dataclass(frozen=True)
class ConfigDifference:
    """One added, removed, or changed leaf with material classification."""

    key: str; left: ConfigValue | None; right: ConfigValue | None; threshold_bearing: bool; redacted: bool


@dataclass(frozen=True)
class ConfigDiff:
    """The complete machine-readable delta between two sealed configs."""

    left_hash: str; right_hash: str; added: tuple[ConfigDifference, ...]; removed: tuple[ConfigDifference, ...]
    changed: tuple[ConfigDifference, ...]; redacted: tuple[ConfigDifference, ...]

    @property
    def is_different(self) -> bool: return bool(self.added or self.removed or self.changed)


def _redacted(value: object) -> bool:
    return isinstance(value, Mapping) and value.get("redacted") is True and isinstance(value.get("rule_version"), str)


def _material(key: str) -> bool:
    normalized = key.replace(".", "_")
    leaf = normalized.rsplit(".", 1)[-1].rsplit("_", 1)[-1]
    return key.startswith("artifact_versions.") or leaf in {"threshold", "seed", "lookback", "horizon"} or any(field in normalized for field in _THRESHOLD_FIELDS)


def _flatten(prefix: str, value: object, provenance: ConfigProvenance, output: dict[str, ConfigValue]) -> None:
    if isinstance(value, Mapping) and not _redacted(value):
        for key, item in value.items(): _flatten(f"{prefix}.{key}" if prefix else str(key), item, provenance, output)
        return
    output[prefix] = ConfigValue(prefix, value, provenance)


def _configuration_values(config: ResolvedConfig) -> dict[str, ConfigValue]:
    artifact = config.artifact; values = artifact["values"]; overrides = artifact["overrides"]; versions = artifact["artifact_versions"]
    profile = artifact["profile"]; defaults = artifact["defaults"]; provenance = artifact["provenance"]
    assert all(isinstance(item, Mapping) for item in (values, overrides, versions, profile, defaults, provenance))
    result: dict[str, ConfigValue] = {}
    for field, value in values.items():
        origin = provenance.get(field)
        assert isinstance(origin, Mapping)
        source = str(origin.get("source", ""))
        result_value = ConfigProvenance(source, str(origin.get("value", "")) or None, origin.get("id"), origin.get("version"), str(profile["content_hash"]) if source == "profile" else None)
        _flatten("values", {field: value}, result_value, result)
    for field, value in overrides.items(): _flatten(f"overrides.{field}", value, ConfigProvenance("override", "explicit"), result)
    _flatten("artifact_versions", versions, ConfigProvenance(source="artifact_versions"), result)
    _flatten("profile", profile, ConfigProvenance(source="profile"), result)
    _flatten("defaults", defaults, ConfigProvenance(source="defaults"), result)
    result["redaction_rule.version"] = ConfigValue("redaction_rule.version", artifact["redaction_rule"], ConfigProvenance(source="redaction_rule"))  # type: ignore[index]
    result["schema_version"] = ConfigValue("schema_version", artifact["schema_version"], ConfigProvenance(source="schema"))
    result["resolver_version"] = ConfigValue("resolver_version", artifact["resolver_version"], ConfigProvenance(source="resolver"))
    return result


def _difference(key: str, left: ConfigValue | None, right: ConfigValue | None) -> ConfigDifference:
    return ConfigDifference(key, left, right, _material(key), _redacted(left.value if left else None) or _redacted(right.value if right else None))


def diff_config(left: ResolvedConfig, right: ResolvedConfig) -> ConfigDiff:
    """Compare effective values, explicit provenance, redactions, and versions."""

    left_values = _configuration_values(left); right_values = _configuration_values(right)
    added: list[ConfigDifference] = []; removed: list[ConfigDifference] = []; changed: list[ConfigDifference] = []; redacted: list[ConfigDifference] = []
    for key in sorted(left_values.keys() | right_values.keys()):
        left_value, right_value = left_values.get(key), right_values.get(key)
        difference: ConfigDifference | None = None
        if left_value is None: difference = _difference(key, None, right_value); added.append(difference)
        elif right_value is None: difference = _difference(key, left_value, None); removed.append(difference)
        elif left_value != right_value: difference = _difference(key, left_value, right_value); changed.append(difference)
        if difference is not None and difference.redacted: redacted.append(difference)
    return ConfigDiff(left.config_hash, right.config_hash, tuple(added), tuple(removed), tuple(changed), tuple(redacted))


__all__ = ["ConfigDiff", "ConfigDifference", "ConfigProvenance", "ConfigValue", "diff_config"]
