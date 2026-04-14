import argparse
from pathlib import Path

import numpy as np


def fit_ridge(X, y, alpha):
    ones = np.ones((X.shape[0], 1), dtype=np.float32)
    Xb = np.concatenate([X, ones], axis=1)
    xtx = Xb.T @ Xb
    reg = alpha * np.eye(xtx.shape[0], dtype=np.float32)
    xty = Xb.T @ y.reshape(-1, 1)
    w = np.linalg.solve(xtx + reg, xty).reshape(-1)
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--alpha", type=float, default=5.0)
    ap.add_argument("--clip", type=float, default=10.0)
    args = ap.parse_args()

    data = np.load(args.data)
    X = data["X"].astype(np.float32)
    Y = data["Y"].astype(np.float32)
    Q = data["Q"].astype(np.int32)

    num_qu = int(Q.max()) + 1
    W = np.zeros((num_qu, X.shape[1] + 1), dtype=np.float32)
    counts = np.zeros(num_qu, dtype=np.int32)

    for qu in range(num_qu):
        idx = np.where(Q == qu)[0]
        counts[qu] = len(idx)
        if len(idx) < 50:
            continue
        w = fit_ridge(X[idx], Y[idx], args.alpha)
        W[qu, :] = w

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, W=W, clip=args.clip, counts=counts)
    print(f"Wrote model: {out_path}")


if __name__ == "__main__":
    main()
