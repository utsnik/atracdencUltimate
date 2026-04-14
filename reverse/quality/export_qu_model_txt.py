import argparse
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Input .npz with W, clip")
    ap.add_argument("--out", required=True, help="Output .txt for C++ loader")
    args = ap.parse_args()

    data = np.load(args.model)
    W = data["W"]
    clip = float(data["clip"])
    num_qu, row = W.shape
    num_feat = row - 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"{num_qu} {num_feat} {clip}\n")
        for q in range(num_qu):
            row_vals = " ".join(f"{v:.8f}" for v in W[q])
            f.write(row_vals + "\n")
    print(f"Wrote model: {out_path}")


if __name__ == "__main__":
    main()
