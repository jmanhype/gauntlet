"""GAUNTLET core package and stable integrity API."""

from .contracts import (
    CanonicalJSONError,
    ExclusiveCreationError,
    IntegrityFailure,
    ManifestVerification,
    ValidationError,
    ValidationResult,
)

__version__ = "0.1.0"
__all__ = [
    "CanonicalJSONError",
    "ExclusiveCreationError",
    "IntegrityFailure",
    "ManifestVerification",
]
