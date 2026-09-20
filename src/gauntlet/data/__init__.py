"""Immutable evidence descriptors and fail-closed dependency evaluation."""
from .dependency import CHECK_ORDER, DependencyError, DependencyEvaluation, DependencyFinding, evaluate_dependencies
from .descriptors import DescriptorError, DescriptorRegistration, EvidenceDescriptor, register_descriptor, validate_descriptor
from .quarantine import QuarantineReason, quarantine_descriptor
DESCRIPTOR_SCHEMA = "gauntlet.evidence.v1"
DEPENDENCY_STATUSES = frozenset(("OK", "DEGRADED", "BLOCKED", "GRAPH_MALFORMED"))
METRIC_VALID = "VALID"
METRIC_DEGRADED = "DEGRADED"
METRIC_INVALID = "INVALID"
__all__ = ["CHECK_ORDER", "DEPENDENCY_STATUSES", "DESCRIPTOR_SCHEMA", "DependencyError", "DependencyEvaluation", "DependencyFinding", "DescriptorError", "DescriptorRegistration", "EvidenceDescriptor", "METRIC_DEGRADED", "METRIC_INVALID", "METRIC_VALID", "QuarantineReason", "evaluate_dependencies", "quarantine_descriptor", "register_descriptor", "validate_descriptor"]
