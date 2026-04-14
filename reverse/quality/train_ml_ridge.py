import argparse
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to .npz with X (frames x bins) and Y (frames x bins)")
    ap.add_argument("--out", required=True, help="Output model .npz")
    ap.add_argument("--alpha", type=float, default=1.0, help="Ridge regularization strength")
    ap.add_argument("--clip", type=float, default=0.6, help="Max abs log10 correction")
    args = ap.parse_args()

    data = np.load(args.data)
    X = data["X"].astype(np.float32)
    Y = data["Y"].astype(np.float32)

    # Add bias term
    ones = np.ones((X.shape[0], 1), dtype=np.float32)
    Xb = np.concatenate([X, ones], axis=1)

    # Ridge: W = (X^T X + alpha I)^-1 X^T Y
    xtx = Xb.T @ Xb
    reg = args.alpha * np.eye(xtx.shape[0], dtype=np.float32)
    xty = Xb.T @ Y
    W = np.linalg.solve(xtx + reg, xty)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, W=W, clip=args.clip)
    print(f"Wrote model: {out_path}")


if __name__ == "__main__":
    main()
