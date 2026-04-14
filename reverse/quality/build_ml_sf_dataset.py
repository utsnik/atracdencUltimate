import argparse
import json
from pathlib import Path

import numpy as np

from at3tool_parse import parse_at3_file


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--dump", required=True, help="atracdenc_frames.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--at3tool-dir", required=True, help="dir with at3tool outputs (*.at3)")
    args = ap.parse_args()

    workdir = Path(args.workdir)
    in_dir = workdir / "input"
    out_dir = Path(args.at3tool_dir)

    dump_items = load_jsonl(args.dump)
    if not dump_items:
        raise RuntimeError("Dump file is empty")

    wavs = sorted(in_dir.glob("*.wav"))
    if not wavs:
        raise RuntimeError("No input wavs")

    X_list = []
    Y_list = []
    Q_list = []
    meta = []

    cursor = 0
    for wav in wavs:
        at3_path = out_dir / f"{wav.stem}.at3tool.at3"
        if not at3_path.exists():
            continue
        frames = parse_at3_file(at3_path)
        if not frames:
            continue
        num_frames = len(frames)
        dump_slice = dump_items[cursor: cursor + num_frames]
        cursor += num_frames
        if len(dump_slice) != num_frames:
            break

        for i in range(num_frames):
            d = dump_slice[i]
            f = frames[i]
            num_qu = min(d["num_qu"], f["num_qu"])
            for qu in range(num_qu):
                log_energy = np.log10(max(d["max_energy"][0][qu], 1e-8))
                sf_enc = d["sf_idx"][qu][0]
                sf_tgt = f["sf_idx"][qu]
                X_list.append([log_energy, float(sf_enc)])
                Y_list.append(float(sf_tgt))
                Q_list.append(qu)

        meta.append({
            "input": str(wav),
            "frames": int(num_frames),
        })

    if not X_list:
        raise RuntimeError("No samples built")

    X = np.asarray(X_list, dtype=np.float32)
    Y = np.asarray(Y_list, dtype=np.float32)
    Q = np.asarray(Q_list, dtype=np.int32)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, X=X, Y=Y, Q=Q)

    meta_path = out_path.with_suffix(".json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump({"items": meta}, f, indent=2)

    print(f"Wrote dataset: {out_path}")
    print(f"Wrote meta: {meta_path}")


if __name__ == "__main__":
    main()
