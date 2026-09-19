"""A tiny, dependency-free writer for complete, non-null Phase 1 tables."""

from __future__ import annotations

import struct
from collections.abc import Mapping, Sequence
from typing import Any

_TYPE = {"int64": 2, "double": 5, "string": 6}


def _varint(value: int) -> bytes:
    unsigned = value & 0xFFFFFFFFFFFFFFFF
    result = bytearray()
    while unsigned > 0x7F:
        result.append((unsigned & 0x7F) | 0x80)
        unsigned >>= 7
    return bytes(result + bytearray((unsigned,)))


def _field(identifier: int, kind: int, value: bytes, previous: list[int]) -> bytes:
    delta = (identifier - previous[0]) % 16
    previous[0] = identifier
    return (bytes(((delta << 4) | kind,)) if delta else bytes((kind,))) + value


def _i32(value: int) -> bytes:
    return _varint((value << 1) ^ (value >> 63))


def _string(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return _varint(len(encoded)) + encoded


def _list_header(size: int, kind: int) -> bytes:
    return bytes(((size << 4) | kind,)) if size <= 14 else bytes((0xF0 | kind,)) + _varint(size)


def _struct(fields: bytes) -> bytes:
    return fields + b"\x00"


def _header(fields: list[tuple[int, int, bytes]]) -> bytes:
    previous = [0]
    return _struct(b"".join(_field(*item, previous) for item in fields))


def _column(name: str, kind: str, rows: Sequence[Mapping[str, Any]]) -> bytes:
    if kind == "int64":
        values = b"".join(struct.pack("<q", int(row[name])) for row in rows)
    elif kind == "double":
        values = b"".join(struct.pack("<d", float(row[name])) for row in rows)
    else:
        values = b"".join(struct.pack("<I", len(item := str(row[name]).encode("utf-8"))) + item for row in rows)
    page = _struct(_field(1, 5, _i32(len(rows)), [0]) + _field(2, 5, _i32(0), [1]) + _field(3, 5, _i32(3), [2]) + _field(4, 5, _i32(3), [3]))
    header = _header([(1, 5, _i32(0)), (2, 5, _i32(len(values))), (3, 5, _i32(len(values))), (5, 12, page)])
    return header + values


def write_parquet(rows: Sequence[Mapping[str, Any]], schema: Mapping[str, str]) -> bytes:
    """Return one uncompressed required-column Parquet file using PLAIN pages."""

    if not rows or not schema or len(schema) > 14:
        raise ValueError("Parquet output requires 1..14 columns and at least one row")
    columns: list[tuple[str, str, bytes]] = []
    for name, kind in schema.items():
        if kind not in _TYPE:
            raise ValueError(f"unsupported Parquet type: {kind}")
        chunk = _column(name, kind, rows)
        columns.append((name, kind, chunk))
    previous = [0]
    root = _field(4, 8, _string("schema"), previous) + _field(5, 5, _i32(len(schema)), previous)
    elements = [_struct(root)]
    for name, kind, _ in columns:
        previous = [0]
        leaf = _field(1, 5, _i32(_TYPE[kind]), previous) + _field(3, 5, _i32(0), previous) + _field(4, 8, _string(name), previous)
        elements.append(_struct(leaf + (_field(6, 5, _i32(0), previous) if kind == "string" else b"")))
    chunks = [chunk for _, _, chunk in columns]
    group: list[bytes] = []
    for index, (name, kind, chunk) in enumerate(columns):
        offset = 4 + sum(len(item) for item in chunks[:index])
        previous = [0]
        metadata = _struct(
            _field(1, 5, _i32(_TYPE[kind]), previous) + _field(2, 9, _list_header(2, 5) + _i32(0) + _i32(3), previous)
            + _field(3, 9, _list_header(1, 8) + _string(name), previous) + _field(4, 5, _i32(0), previous)
            + _field(5, 6, _varint(len(rows) << 1), previous) + _field(6, 6, _varint(len(chunk) << 1), previous)
            + _field(7, 6, _varint(len(chunk) << 1), previous) + _field(9, 6, _varint(offset << 1), previous)
        )
        previous = [0]
        group.append(_struct(_field(2, 6, _varint(offset << 1), previous) + _field(3, 12, metadata, previous)))
    previous = [0]
    row_group = _struct(_field(1, 9, _list_header(len(group), 12) + b"".join(group), previous) + _field(2, 6, _varint(sum(map(len, chunks)) << 1), previous) + _field(3, 6, _varint(len(rows) << 1), previous))
    previous = [0]
    footer = _struct(
        _field(1, 5, _i32(1), previous) + _field(2, 9, _list_header(len(elements), 12) + b"".join(elements), previous)
        + _field(3, 6, _varint(len(rows) << 1), previous) + _field(4, 9, _list_header(1, 12) + row_group, previous)
        + _field(6, 8, _string("gauntlet-minimal-v1"), previous)
    )
    return b"PAR1" + b"".join(chunks) + footer + struct.pack("<I", len(footer)) + b"PAR1"


__all__ = ["write_parquet"]
