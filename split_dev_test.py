"""
Chia dev (70%) / test (30%) THEO MÃ ĐƠN GỐC, không theo từng ảnh, phân tầng theo nguồn (thật / tổng hợp).
    python split_dev_test.py --gold eval/labels.csv --out eval/data
Ảnh s001__ro_net, s001__sim_mo... là CÙNG một đơn thuốc; chia theo ảnh sẽ làm lộ đáp án sang tập test.
Sinh split_dev.txt, split_test.txt (mỗi dòng 1 mã đơn) và split_images_*.txt.
"""
import argparse
import random
from pathlib import Path

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--gold", required=True)
ap.add_argument("--out", default="evaluation/data")
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--test-frac", type=float, default=0.3)
a = ap.parse_args()

g = pd.read_csv(a.gold, dtype=str, encoding="utf-8-sig")
if "image_id" not in g.columns and "id" in g.columns:
    g = g.rename(columns={"id": "image_id"})
g = g.drop_duplicates("image_id")
g["base_id"] = g["image_id"].str.split("__").str[0]
g["source"] = g["base_id"].apply(lambda x: "tonghop" if x.startswith("s") else "that")
rng = random.Random(a.seed)
dev, test = [], []
for src, grp in g.groupby("source"):
    ids = sorted(grp["base_id"].unique())
    rng.shuffle(ids)
    n_test = max(1, round(len(ids) * a.test_frac)) if len(ids) >= 2 else 0
    test += ids[:n_test]
    dev += ids[n_test:]
assert not (set(dev) & set(test)), "một mã đơn nằm ở cả dev và test"
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "split_dev.txt").write_text("\n".join(sorted(dev)) + "\n", encoding="utf-8")
(out / "split_test.txt").write_text("\n".join(sorted(test)) + "\n", encoding="utf-8")
for name, ids in (("dev", dev), ("test", test)):
    imgs = sorted(g.loc[g["base_id"].isin(ids), "image_id"])
    (out / f"split_images_{name}.txt").write_text("\n".join(imgs) + "\n", encoding="utf-8")
print(f"dev={len(dev)} đơn, test={len(test)} đơn (seed={a.seed}); thật: dev={sum(not x.startswith('s') for x in dev)}, test={sum(not x.startswith('s') for x in test)}")
