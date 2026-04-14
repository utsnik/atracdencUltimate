#!/usr/bin/env python3
"""
Fix RIFF/data chunk sizes for ATRAC3 .at3.wav files.

Usage:
  python tools/fix_at3_riff_header.py youtopia_song*.at3.wav
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def fix_file(path: Path, min_size: int) -> tuple[bool, str]:
    b = bytearray(path.read_bytes())
    if len(b) < max(64, min_size):
        return False, "too_small"
    if b[:4] != b"RIFF" or b[8:12] != b"WAVE":
        return False, "not_riff_wave"

    off = 12
    data_off = None
    fmt_off = None
    fmt_sz = 0
    fact_off = None
    while off + 8 <= len(b):
        cid = bytes(b[off : off + 4])
        sz = struct.unpack_from("<I", b, off + 4)[0]
        if cid == b"fmt ":
            fmt_off = off + 8
            fmt_sz = sz
        elif cid == b"fact":
            fact_off = off + 8
        elif cid == b"data":
            data_off = off
            break
        n_off = off + 8 + sz + (sz & 1)
        if n_off <= off or n_off > len(b):
            break
        off = n_off

    if data_off is None:
        return False, "no_data_chunk"

    actual_data = len(b) - (data_off + 8)
    struct.pack_into("<I", b, 4, len(b) - 8)
    struct.pack_into("<I", b, data_off + 4, actual_data)

    # Keep fact sample count coherent if present.
    if fact_off is not None and fact_off + 4 <= len(b):
        block_align = 384
        if fmt_off is not None and fmt_sz >= 16 and fmt_off + 14 <= len(b):
            block_align = struct.unpack_from("<H", b, fmt_off + 12)[0] or 384
        frames = actual_data // block_align if block_align else 0
        struct.pack_into("<I", b, fact_off, frames * 1024)

    path.write_bytes(b)
    return True, f"fixed data={actual_data}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="glob(s) or file path(s)")
    ap.add_argument("--min-size", type=int, default=1_000_000, help="skip files smaller than this many bytes")
    args = ap.parse_args()

    paths: list[Path] = []
    for pat in args.files:
        p = Path(pat)
        if p.exists():
            paths.append(p)
            continue
        paths.extend(sorted(Path(".").glob(pat)))

    seen = set()
    for p in paths:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        ok, msg = fix_file(p, args.min_size)
        print(f"{p}: {msg}")


if __name__ == "__main__":
    main()

