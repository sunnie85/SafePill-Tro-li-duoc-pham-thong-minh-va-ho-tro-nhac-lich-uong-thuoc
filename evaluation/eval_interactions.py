#!/usr/bin/env python3
"""
Chấm khả năng phát hiện tương tác thuốc của SafePill so với interaction_gold.csv.

    python evaluation/eval_interactions.py [--gold evaluation/data/interaction_gold.csv]

Mỗi cặp rơi vào 1 trong 3 trạng thái của hệ thống:
  PHÁT HIỆN      : check_interaction trả về kết quả.
  KHÔNG NHẬN DIỆN: ít nhất 1 thuốc không có trong CSDL -> hệ thống phải báo "chưa kiểm tra được".
  IM LẶNG        : cả hai thuốc được nhận diện nhưng cặp không có trong CSDL -> hệ thống trả "không thấy cảnh báo".
Với cặp CÓ tương tác thật (expected=yes), IM LẶNG là trường hợp nguy hiểm nhất.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from safepill_core import check_interaction, normalize_drug_name  # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p, d = k / n, 1 + z * z / n
    c, m = p + z * z / (2 * n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - m) / d), min(1.0, (c + m) / d)


def fmt(k, n):
    if n == 0:
        return "n/a (0)"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% (CI {100 * lo:.0f}–{100 * hi:.0f}%)"


def classify(a, b):
    na, nb = normalize_drug_name(a)[0], normalize_drug_name(b)[0]
    if check_interaction(a, b):
        return "PHÁT HIỆN", na, nb
    if not na or not nb:
        return "KHÔNG NHẬN DIỆN", na, nb
    return "IM LẶNG", na, nb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default=str(ROOT / "data" / "interaction_gold.csv"))
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.gold, newline="", encoding="utf-8-sig")))
    res = []
    for r in rows:
        state, na, nb = classify(r["drug_a"], r["drug_b"])
        res.append({**r, "state": state, "a_ok": bool(na), "b_ok": bool(nb)})

    pos = [r for r in res if r["expected"] == "yes"]
    neg = [r for r in res if r["expected"] == "no"]
    indb = [r for r in pos if r["nhom"] == "trong_csdl"]
    indep = [r for r in pos if r["nhom"] != "trong_csdl"]          # đối chiếu độc lập, không do CSDL tự dựng
    both_known = [r for r in indep if r["a_ok"] and r["b_ok"]]
    drugs = {x for r in res for x in (r["drug_a"], r["drug_b"])}
    known = {d for d in drugs if normalize_drug_name(d)[0]}

    def n(rs, s):
        return sum(r["state"] == s for r in rs)

    L = ["# Kết quả tương tác thuốc",
         f"_{len(res)} cặp ({len(pos)} có tương tác, {len(neg)} không). Khoảng tin cậy Wilson 95%._", "",
         "## Chỉ số chính (chỉ tính cặp độc lập, KHÔNG tính nhóm `trong_csdl` vì CSDL được dựng từ đó)", "",
         f"- **Recall tổng thể:** {fmt(n(indep, 'PHÁT HIỆN'), len(indep))}",
         f"- **Recall trong phạm vi** (cả hai thuốc được nhận diện): {fmt(n(both_known, 'PHÁT HIỆN'), len(both_known))}",
         f"- Không nhận diện (hệ thống phải báo 'chưa kiểm tra được'): {fmt(n(indep, 'KHÔNG NHẬN DIỆN'), len(indep))}",
         f"- **Bỏ sót im lặng** (thuốc nhận diện nhưng cặp không có, hệ thống nói 'không thấy cảnh báo'): {fmt(n(indep, 'IM LẶNG'), len(indep))}",
         f"- Báo nhầm trên cặp không tương tác: {fmt(n(neg, 'PHÁT HIỆN'), len(neg))}",
         f"- Độ phủ: {len(known)}/{len(drugs)} thuốc trong bộ gold được nhận diện ({100 * len(known) / len(drugs):.0f}%)",
         "", "## Nhóm `trong_csdl` (kiểm tra hồi quy, kết quả hiển nhiên cao)", "",
         f"- Phát hiện: {fmt(n(indb, 'PHÁT HIỆN'), len(indb))}",
         "", "## Chi tiết từng cặp", "",
         "| Thuốc A | Thuốc B | Đáp án | Nhóm | Hệ thống | Đánh giá | Đã xác nhận nguồn |", "|---|---|---|---|---|---|---|"]
    for r in res:
        if r["expected"] == "yes":
            verdict = {"PHÁT HIỆN": "đúng", "KHÔNG NHẬN DIỆN": "bỏ sót nhưng phải báo 'chưa kiểm tra được'",
                       "IM LẶNG": "**BỎ SÓT IM LẶNG**"}[r["state"]]
        else:
            verdict = "**BÁO NHẦM**" if r["state"] == "PHÁT HIỆN" else "đúng"
        L.append(f"| {r['drug_a']} | {r['drug_b']} | {r['expected']} | {r['nhom']} | {r['state']} | {verdict} | {r['da_xac_nhan'] or 'chưa'} |")
    unver = sum(1 for r in res if not r["da_xac_nhan"].strip())
    L += ["", f"> **Chưa xác nhận nguồn:** {unver}/{len(res)} cặp. Phải tra từng cặp trên Drugs.com (hoặc Dược thư) và điền cột `da_xac_nhan` trước khi báo cáo.",
          "> Mẫu nhỏ, khoảng tin cậy rộng; 'không có tương tác' nghĩa là không ghi nhận mức vừa/nặng theo nguồn, không phải bảo đảm an toàn."]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "interaction_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:14]))
    print(f"\nĐã ghi {out / 'interaction_report.md'}")


if __name__ == "__main__":
    main()
