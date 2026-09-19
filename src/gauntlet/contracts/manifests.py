"""Immutable artifact manifest creation and verification."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping

from .canonical import canonical_json, sha256_digest
from .schemas import MANIFEST, validate

@dataclass(frozen=True)
class IntegrityFailure:
    code: str
    message: str
    path: str | None

@dataclass(frozen=True)
class ManifestVerification:
    valid: bool
    file_count: int
    external_count: int
    merkle_root: str | None
    failure: IntegrityFailure | None

class ExclusiveCreationError(RuntimeError):
    """A machine-readable write-once creation rejection."""

    def __init__(self, code: str, message: str, path: Path) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path

def _failed(code: str, message: str, path: str | None = None) -> ManifestVerification:
    return ManifestVerification(False, 0, 0, None, IntegrityFailure(code, message, path))

def _safe_path(raw: str, data_root: Path) -> Path | None:
    posix = PurePosixPath(raw)
    if posix.is_absolute() or ".." in posix.parts or raw != posix.as_posix():
        return None
    root = data_root.resolve()
    candidate = (root / Path(*posix.parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate

def _merkle_root(entries: tuple[Mapping[str, object], ...]) -> str:
    level = [hashlib.sha256(canonical_json(entry)).digest() for entry in entries]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return f"sha256:{level[0].hex()}"

def verify_manifest(manifest_path: Path, data_root: Path) -> ManifestVerification:
    """Verify every embedded and external artifact named by a manifest."""

    try:
        instance: object = json.loads(manifest_path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return _failed("MANIFEST_READ_FAILED", str(error), str(manifest_path))
    result = validate(instance, MANIFEST)
    if not result.valid:
        first = result.errors[0]
        return _failed("SCHEMA_INVALID", first.message, first.path)
    assert isinstance(instance, dict)
    files = instance["files"]
    external = instance["external_artifacts"]
    assert isinstance(files, list) and isinstance(external, list)
    entries: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for raw_entry in (*files, *external):
        assert isinstance(raw_entry, dict)
        raw_path = raw_entry.get("path")
        expected = raw_entry.get("hash")
        if not isinstance(raw_path, str) or not isinstance(expected, str):
            return _failed("SCHEMA_INVALID", "manifest entry is malformed", str(manifest_path))
        candidate = _safe_path(raw_path, data_root)
        if raw_path in seen or candidate is None:
            code = "PATH_DUPLICATE" if raw_path in seen else "PATH_NOT_RELATIVE"
            return _failed(code, "path is duplicated or escapes data_root", raw_path)
        seen.add(raw_path)
        if not candidate.is_file() or candidate.is_symlink():
            return _failed("ARTIFACT_MISSING", "artifact is missing or not a regular file", raw_path)
        actual = sha256_digest(candidate.read_bytes())
        if actual != expected:
            return _failed("ARTIFACT_HASH_MISMATCH", f"expected {expected}, got {actual}", raw_path)
        entries.append(raw_entry)
    if not entries:
        return _failed("MANIFEST_EMPTY", "at least one artifact is required")
    root = _merkle_root(tuple(entries))
    declared = instance.get("merkle_root")
    assert isinstance(declared, str)
    if root != declared:
        return ManifestVerification(False, len(files), len(external), None, IntegrityFailure("MERKLE_ROOT_MISMATCH", f"expected {declared}, got {root}", str(manifest_path)))
    return ManifestVerification(True, len(files), len(external), root, None)

def create_exclusive(destination: Path, data: bytes) -> Path:
    """Create an immutable file once without destructive replacement."""

    if destination.is_symlink() or destination.exists():
        if destination.is_dir() and not destination.is_symlink():
            if any(destination.iterdir()):
                raise ExclusiveCreationError("DESTINATION_NOT_EMPTY", "output directory is not empty", destination)
            destination.rmdir()
        else:
            raise ExclusiveCreationError("ARTIFACT_EXISTS", "immutable artifact already exists", destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor: int | None = None
    created = False
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
        os.fchmod(descriptor, 0o444)
    except FileExistsError as error:
        raise ExclusiveCreationError("ARTIFACT_EXISTS", "artifact was created concurrently", destination) from error
    except BaseException:
        if created and destination.exists():
            destination.unlink()
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return destination
