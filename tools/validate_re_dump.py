#!/usr/bin/env python3
"""
Quick sanity validator for at3tool per-frame dump files.

Flags suspicious/placeholder dumps where key metrics are constant across frames.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return []
    # Allow a metadata line before header.
    start = 1 if lines[0].startswith('"#') or lines[0].startswith("#") else 0
    return list(csv.DictReader(lines[start:]))


def uniq(rows: list[dict[str, str]], key: str) -> int:
    return len({r.get(key, "") for r in rows})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    args = ap.parse_args()

    rows = load_rows(args.csv_path)
    if not rows:
        print("FAIL: no rows")
        raise SystemExit(1)

    checks = {
        "frame_idx": uniq(rows, "frame_idx"),
        "target_bits": uniq(rows, "target_bits"),
        "used_bits": uniq(rows, "used_bits"),
        "complexity": uniq(rows, "complexity"),
        "num_tonals_total": uniq(rows, "num_tonals_total"),
        "attack_ratio": uniq(rows, "attack_ratio"),
        "trigger": uniq(rows, "trigger"),
        "matrix_index": uniq(rows, "matrix_index"),
        "weights": uniq(rows, "weights"),
    }

    print(f"rows={len(rows)}")
    for k, v in checks.items():
        print(f"{k}_unique={v}")

    samples = sorted({r.get("sample", "") for r in rows if r.get("sample", "")})
    sample_fail = False
    for s in samples:
        sub = [r for r in rows if r.get("sample", "") == s]
        c_u = len({r.get("complexity", "") for r in sub})
        t_u = len({r.get("num_tonals_total", "") for r in sub})
        a_u = len({r.get("attack_ratio", "") for r in sub})
        m_u = len({r.get("matrix_index", "") for r in sub})
        w_u = len({r.get("weights", "") for r in sub})
        print(f"sample={s} rows={len(sub)} complexity_u={c_u} tonals_u={t_u} attack_u={a_u} matrix_u={m_u} weights_u={w_u}")
        # Real dumps generally move at least a bit over many frames.
        if len(sub) >= 12 and (c_u <= 1 and t_u <= 1 and a_u <= 1 and m_u <= 1 and w_u <= 1):
            sample_fail = True

    # Heuristic: healthy dumps should vary in several dimensions and within sample.
    varied = sum(1 for k in ("target_bits", "used_bits", "complexity", "num_tonals_total", "attack_ratio", "matrix_index", "weights") if checks[k] > 1)
    if checks["frame_idx"] < 16 or varied < 3 or sample_fail:
        print("FAIL: dump looks synthetic/placeholder (insufficient intra-sample variation).")
        raise SystemExit(2)
    print("PASS: dump looks plausibly dynamic.")


if __name__ == "__main__":
    main()
