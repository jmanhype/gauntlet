"""Versioned, fail-closed evidence dependency evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from gauntlet.contracts.canonical import canonical_json, sha256_digest
from gauntlet.ledger._common import LedgerError, data_root_path, validate_digest

from .descriptors import StoredDescriptor, _duration_seconds, _parse_timestamp, load_descriptor_registry


CHECK_ORDER = ("CONTENT_HASH_AND_SCHEMA", "PROVENANCE_REACHABILITY", "FRESHNESS_AT_AS_OF", "QUALITY_CHECKS", "RECURSIVE_DEPENDENCY_HEALTH", "OBSERVATION_BASIS_ELIGIBILITY", "POLICY_CRITICALITY")


@dataclass(frozen=True)
class DependencyFinding:
    """One machine-readable result from the ordered dependency checks."""

    check: str; code: str; message: str; criticality: str; descriptor_hash: str | None; affected_metrics: tuple[str, ...]


@dataclass(frozen=True)
class DependencyEvaluation:
    """The complete auditable result for one dependency closure."""

    status: str; graph_hash: str; selected_descriptor_hashes: tuple[str, ...]; metric_states: Mapping[str, str]
    affected_metrics: tuple[str, ...]; coverage: float; findings: tuple[DependencyFinding, ...]; quarantined: bool
    evidence_policy_hash: str; as_of: str


class DependencyError(RuntimeError):
    """A machine-readable argument or registry rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message); self.code = code; self.message = message; self.path = path


@dataclass(frozen=True)
class _Edge:
    parent_hash: str; target_hash: str; health_hash: str


def _utc_z(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None: raise DependencyError("ARGUMENT_INVALID", "as_of must be timezone-aware")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _metrics(value: Mapping[str, object]) -> tuple[str, ...]:
    metrics = value.get("downstream_metrics"); assert isinstance(metrics, list)
    return tuple(str(item) for item in metrics)


def _active_by_id(records: dict[str, StoredDescriptor], descriptor_id: str, as_of: datetime) -> StoredDescriptor | None:
    versions = [(effective, stored) for stored in records.values() if stored.value.get("descriptor_id") == descriptor_id and (effective := _parse_timestamp(stored.value["effective_at_utc"])) <= as_of]
    superseded = {stored.value.get("supersedes_descriptor_hash") for _, stored in versions}
    selected = [stored for _, stored in versions if stored.value["descriptor_hash"] not in superseded]
    return max(selected, key=lambda item: _parse_timestamp(item.value["effective_at_utc"])) if selected else None


def _is_digest(value: str) -> bool:
    return len(value) == 71 and value.startswith("sha256:")


def _materialize(records: dict[str, StoredDescriptor], descriptor_ids: tuple[str, ...], as_of: datetime) -> tuple[dict[str, StoredDescriptor], tuple[_Edge, ...], tuple[str, ...], list[str], str | None]:
    selected: dict[str, StoredDescriptor] = {}; edges: list[_Edge] = []; missing: list[str] = []
    visiting: set[str] = set(); visited: set[str] = set()
    postorder: list[str] = []

    def visit(stored: StoredDescriptor) -> str | None:
        descriptor_hash = str(stored.value["descriptor_hash"])
        if descriptor_hash in visiting: return f"dependency cycle includes {descriptor_hash}"
        if descriptor_hash in visited: return None
        visiting.add(descriptor_hash)
        selected[descriptor_hash] = stored
        for dependency in stored.resolved_dependencies:
            if not isinstance(dependency, dict) or not isinstance(dependency.get("descriptor_hash"), str):
                visiting.remove(descriptor_hash)
                return f"malformed resolved dependency on {descriptor_hash}"
            target_hash = dependency["descriptor_hash"]
            target = records.get(target_hash)
            if target is None:
                missing.append(target_hash); edges.append(_Edge(descriptor_hash, target_hash, target_hash)); continue
            active = _active_by_id(records, str(target.value["descriptor_id"]), as_of)
            health_hash = str(active.value["descriptor_hash"]) if active is not None else target_hash
            edges.append(_Edge(descriptor_hash, target_hash, health_hash))
            health = records.get(health_hash)
            if health is None: missing.append(health_hash); continue
            cycle = visit(health)
            if cycle is not None: visiting.remove(descriptor_hash); return cycle
        visiting.remove(descriptor_hash)
        visited.add(descriptor_hash)
        postorder.append(descriptor_hash)
        return None

    for descriptor_id in descriptor_ids:
        stored = records.get(descriptor_id) if _is_digest(descriptor_id) else _active_by_id(records, descriptor_id, as_of)
        if stored is None:
            missing.append(descriptor_id)
            continue
        cycle = visit(stored)
        if cycle is not None:
            return {}, (), (), [], cycle
    return selected, tuple(edges), tuple(missing), postorder, None


def _finding(check: str, code: str, message: str, stored: StoredDescriptor, metrics: tuple[str, ...]) -> DependencyFinding:
    criticality = str(stored.value["criticality"])
    return DependencyFinding(check, code, message, criticality, str(stored.value["descriptor_hash"]), tuple(sorted(set(metrics))))


def _local_findings(stored: StoredDescriptor, as_of: datetime) -> tuple[DependencyFinding, ...]:
    value = stored.value; findings: list[DependencyFinding] = []; metrics = _metrics(value)
    source = value["source"]; assert isinstance(source, dict)
    if not isinstance(source.get("collector"), str) or not source["collector"].strip() or not isinstance(source.get("uri_or_lineage"), str) or not source["uri_or_lineage"].strip():
        findings.append(_finding(CHECK_ORDER[1], "PROVENANCE_UNREACHABLE", "source collector or lineage is unavailable", stored, metrics))
    freshness = value["freshness"]; assert isinstance(freshness, dict)
    watermark = _parse_timestamp(freshness.get("watermark_at"))
    max_age = _duration_seconds(freshness.get("max_age"))
    if watermark is None or watermark > as_of:
        findings.append(_finding(CHECK_ORDER[2], "FRESHNESS_INVALID", "watermark is after the declared as_of", stored, metrics))
    elif max_age is None or (as_of - watermark).total_seconds() > max_age:
        findings.append(_finding(CHECK_ORDER[2], "FRESHNESS_STALE", "watermark exceeds max_age at as_of", stored, metrics))
    quality = value["quality"]; assert isinstance(quality, dict)
    if quality.get("state") != "VALID":
        findings.append(_finding(CHECK_ORDER[3], f"QUALITY_{str(quality.get('state'))}", "descriptor quality state is not VALID", stored, metrics))
    checks = quality.get("checks", []); assert isinstance(checks, list)
    if any(not isinstance(check, dict) or check.get("status") != "PASS" for check in checks):
        findings.append(_finding(CHECK_ORDER[3], "QUALITY_CHECK_FAILED", "at least one declared quality check did not pass", stored, metrics))
    return tuple(findings)


def _graph_hash(roots: tuple[str, ...], as_of: str, policy_hash: str, selected: dict[str, StoredDescriptor], edges: tuple[_Edge, ...], missing: tuple[str, ...]) -> str:
    graph = {"as_of": as_of, "edges": [{"from": edge.parent_hash, "health_at": edge.health_hash, "to": edge.target_hash} for edge in sorted(edges, key=lambda item: (item.parent_hash, item.target_hash, item.health_hash))], "evidence_policy_hash": policy_hash, "missing": sorted(missing), "roots": list(roots), "selected": sorted(selected)}
    return sha256_digest(canonical_json(graph))


def _malformed(roots: tuple[str, ...], as_of: str, policy_hash: str, required_metrics: tuple[str, ...], message: str) -> DependencyEvaluation:
    metric_states = {metric: "INVALID" for metric in required_metrics}
    finding = DependencyFinding(CHECK_ORDER[4], "GRAPH_MALFORMED", message, "GATE_CRITICAL", None, required_metrics)
    graph = {"as_of": as_of, "error": "GRAPH_MALFORMED", "evidence_policy_hash": policy_hash, "roots": list(roots)}
    return DependencyEvaluation("GRAPH_MALFORMED", sha256_digest(canonical_json(graph)), (), metric_states, required_metrics, 0.0, (finding,), False, policy_hash, as_of)


def evaluate_dependencies(descriptor_ids: list[str], as_of: datetime, evidence_policy_hash: str, required_metrics: set[str]) -> DependencyEvaluation:
    """Evaluate complete descriptor closure in the architecture's fixed check order."""

    roots = tuple(sorted(set(descriptor_ids)))
    metrics = tuple(sorted(required_metrics))
    if not roots or any(not isinstance(root, str) or not root.strip() for root in roots):
        raise DependencyError("ARGUMENT_INVALID", "at least one descriptor id is required", "$.descriptor_ids")
    if any(not isinstance(metric, str) or not metric.strip() for metric in metrics):
        raise DependencyError("ARGUMENT_INVALID", "required metrics must be non-empty strings", "$.required_metrics")
    try: validate_digest(evidence_policy_hash, "$.evidence_policy_hash")
    except LedgerError as error:
        raise DependencyError(error.code, error.message, error.path or "$.evidence_policy_hash") from error
    as_of_z = _utc_z(as_of)
    try: records = load_descriptor_registry(data_root_path(None))
    except Exception as error:
        if hasattr(error, "code") and getattr(error, "code") in {"CONTENT_HASH_MISMATCH", "CONTENT_MISSING", "DESCRIPTOR_UNVERIFIED"}:
            finding = DependencyFinding(CHECK_ORDER[0], "REPLAY_FAILED", str(error), "GATE_CRITICAL", None, metrics)
            graph = {"as_of": as_of_z, "error": "DESCRIPTOR_UNVERIFIED", "evidence_policy_hash": evidence_policy_hash, "roots": list(roots)}
            return DependencyEvaluation("BLOCKED", sha256_digest(canonical_json(graph)), (), {metric: "INVALID" for metric in metrics}, metrics, 0.0, (finding,), False, evidence_policy_hash, as_of_z)
        return _malformed(roots, as_of_z, evidence_policy_hash, metrics, str(error))
    selected, edges, missing, postorder, cycle = _materialize(records, roots, as_of)
    digest = _graph_hash(roots, as_of_z, evidence_policy_hash, selected, edges, missing)
    if cycle is not None:
        return _malformed(roots, as_of_z, evidence_policy_hash, metrics, cycle)

    local = {descriptor_hash: _local_findings(stored, as_of) for descriptor_hash, stored in selected.items()}
    propagated = {descriptor_hash: () for descriptor_hash in selected}; affected = {descriptor_hash: set() for descriptor_hash in selected}
    for descriptor_hash, findings in local.items():
        affected[descriptor_hash].update(*(finding.affected_metrics for finding in findings) or ())

    reverse: dict[str, list[str]] = {descriptor_hash: [] for descriptor_hash in selected}
    for edge in edges:
        reverse[edge.parent_hash].append(edge.target_hash)
        if edge.health_hash != edge.target_hash and edge.health_hash in selected:
            reverse[edge.parent_hash].append(edge.health_hash)

    order = postorder
    for parent_hash in order:
        parent = selected[parent_hash]; parent_metrics = _metrics(parent.value)
        for child_hash in reverse.get(parent_hash, []):
            child_findings = (*local.get(child_hash, ()), *propagated.get(child_hash, ()))
            for child_finding in child_findings:
                criticality = "NON_CRITICAL" if child_finding.criticality == "NON_CRITICAL" else "GATE_CRITICAL"
                child_metrics = set(child_finding.affected_metrics)
                scope = child_metrics | set(parent_metrics) if criticality == "GATE_CRITICAL" else child_metrics
                propagated[parent_hash] += (DependencyFinding(CHECK_ORDER[4], child_finding.code, f"dependency {child_hash} failed: {child_finding.message}", criticality, parent_hash, tuple(sorted(scope))),)
                affected[parent_hash].update(scope)

    findings: list[DependencyFinding] = []
    for descriptor_hash in sorted(selected):
        findings.extend(local[descriptor_hash])
        findings.extend(propagated[descriptor_hash])
        stored = selected[descriptor_hash]
        observed_metrics = set(_metrics(stored.value)) & set(metrics)
        if stored.value.get("observation_basis") == "MODELED" and observed_metrics:
            findings.append(_finding(CHECK_ORDER[5], "OBSERVATION_BASIS_INVALID", "MODELED evidence cannot satisfy an observed-outcome rule", stored, tuple(observed_metrics)))
            affected[descriptor_hash].update(observed_metrics)
        if stored.value.get("criticality") == "UNKNOWN":
            findings.append(_finding(CHECK_ORDER[6], "CRITICALITY_UNKNOWN", "unknown criticality is gate-critical until classified", stored, _metrics(stored.value)))
            affected[descriptor_hash].update(_metrics(stored.value))
    if missing:
        findings.append(DependencyFinding(CHECK_ORDER[4], "DEPENDENCY_MISSING", f"missing descriptor inputs: {sorted(missing)}", "GATE_CRITICAL", None, metrics))
    findings.sort(key=lambda finding: CHECK_ORDER.index(finding.check))

    states: dict[str, str] = {metric: "DEGRADED" for metric in metrics}
    for descriptor_hash, stored in selected.items():
        for metric in _metrics(stored.value):
            if metric in states and metric not in affected[descriptor_hash]:
                states[metric] = "VALID"
    for finding in findings:
        if finding.criticality == "NON_CRITICAL":
            continue
        for metric in finding.affected_metrics:
            if metric in states:
                states[metric] = "INVALID"
    invalid = any(state == "INVALID" for state in states.values()) or any(finding.criticality != "NON_CRITICAL" and not finding.affected_metrics for finding in findings)
    degraded = any(state == "DEGRADED" for state in states.values())
    status = "BLOCKED" if invalid else "DEGRADED" if degraded else "OK"
    valid_count = sum(state == "VALID" for state in states.values())
    coverage = valid_count / len(metrics) if metrics else (1.0 if status == "OK" else 0.0)
    affected_metrics = tuple(metric for metric in metrics if states[metric] != "VALID")
    quarantined = any(stored.value.get("quality", {}).get("state") == "QUARANTINED" for stored in selected.values())
    return DependencyEvaluation(status, digest, tuple(sorted(selected)), dict(states), affected_metrics, coverage, tuple(findings), quarantined, evidence_policy_hash, as_of_z)


__all__ = ["CHECK_ORDER", "DependencyError", "DependencyEvaluation", "DependencyFinding", "evaluate_dependencies"]
