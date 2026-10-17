"""Đo độ chính xác đọc đơn thuốc theo từng điều kiện ảnh, kèm khoảng tin cậy 95%.

    export GEMINI_API_KEY="..."
    python tools/eval_pipeline.py --truth eval/labels.csv --images eval/images --out eval/results
    (tuỳ chọn) --blind eval/labels_blind.csv   # đo độ đồng thuận giữa 2 người dán nhãn

truth CSV: cột id, ten_thuoc, lieu_luong, thoi_diem (mỗi dòng 1 thuốc). Ảnh đặt tên <id>__<điều_kiện>.jpg.
Dùng đúng PRESCRIPTION_VISION_PROMPT và check_image_quality trong safepill_core.py.
Ảnh bị bộ kiểm tra chặn tính riêng ("chặn"), không tính là đọc sai.
"""
import argparse, csv, difflib, json, math, os, re, sys, time, unicodedata
from collections import defaultdict

EXTS = (".jpg", ".jpeg", ".png", ".webp")


class QuotaStop(Exception):
    """Hết hạn mức gọi API trong ngày (hoặc đạt --max-calls): dừng sớm, giữ kết quả đã đo."""


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def fmt(k, n):
    if n == 0:
        return "-"
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.0f}% ({100 * lo:.0f}-{100 * hi:.0f}) n={n}"


def is_unsure(p):
    """Dòng AI tự gắn 'Chưa chắc chắn' = người dùng sẽ thấy cảnh báo ở bước đối chiếu."""
    return str(p.get("Chưa chắc chắn", "")).strip().lower() in ("có", "co", "true", "yes")


FORM_WORDS = r"(viên|vien|nén|nen|gói|goi|ống|ong|chai|lọ|lo|hộp|hop|tablet|capsule|cap)"
STRENGTH_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|μg|ug|g|ml|iu|ui|%)", re.I)


def core_name(s):
    """Tên hoạt chất để so sánh: bỏ nội dung trong ngoặc (biệt dược), hàm lượng, dạng bào chế, số thứ tự."""
    s = re.sub(r"\(.*?\)", " ", str(s or ""))
    s = STRENGTH_RE.sub(" ", s)
    s = re.sub(r"\b" + FORM_WORDS + r"\b", " ", s, flags=re.I)
    return norm(s)


def strengths(s):
    """Tập hàm lượng chuẩn hoá trong chuỗi, ví dụ 'Paracetamol 500 mg' -> {'500mg'}."""
    out = set()
    for num, unit in STRENGTH_RE.findall(str(s or "")):
        unit = unit.lower().replace("µg", "mcg").replace("μg", "mcg").replace("ug", "mcg")
        num = num.replace(",", ".")
        if "." in num:
            num = num.rstrip("0").rstrip(".")
        out.add(num + unit)
    return out


def name_match(a, b):
    ca, cb = core_name(a), core_name(b)
    return bool(ca) and bool(cb) and (ca == cb or difflib.SequenceMatcher(None, ca, cb).ratio() >= 0.88)


def score(truth_rows, preds, any_flag=False):
    """Chấm theo hoạt chất và hàm lượng đã tách ra, không đòi khớp từng ký tự.
    - name_ok: đúng hoạt chất (bỏ biệt dược/hàm lượng/dạng bào chế).
    - dose_ok: hàm lượng đúng; wrong_dose: máy đưa ra hàm lượng nhưng KHÁC đáp án (nguy hiểm).
    - serious: thuốc tìm thấy nhưng sai tên HOẶC sai hàm lượng."""
    r = dict(n=len(truth_rows), found=0, name_ok=0, dose_ok=0, time_ok=0, missed=0,
             wrong_name=0, wrong_dose=0, serious=0, dose_missing=0,
             missed_silent=0, serious_silent=0)
    bad = []
    used = set()
    for t in truth_rows:
        best, br = None, 0.0
        for i, p in enumerate(preds):
            if i in used:
                continue
            x = difflib.SequenceMatcher(None, core_name(t["ten_thuoc"]), core_name(p.get("Tên thuốc", ""))).ratio()
            if x > br:
                best, br = i, x
        if best is None or br < 0.6:
            r["missed"] += 1; bad.append(f"BỎ SÓT: {t['ten_thuoc']} {t['lieu_luong']}")
            if not any_flag:
                r["missed_silent"] += 1  # bỏ sót mà ảnh không có bất kỳ cảnh báo nào
            continue
        used.add(best); p = preds[best]; r["found"] += 1
        nok = name_match(t["ten_thuoc"], p.get("Tên thuốc", ""))
        r["name_ok"] += nok; r["wrong_name"] += (not nok)
        ts = strengths(t["lieu_luong"]) or strengths(t["ten_thuoc"])
        ps = strengths(p.get("Liều lượng", "")) | strengths(p.get("Tên thuốc", ""))
        if not ts:
            dok, dwrong = norm(t["lieu_luong"]) == norm(p.get("Liều lượng", "")), False
        elif not ps:
            dok, dwrong = False, False; r["dose_missing"] += 1
        else:
            dok = bool(ts & ps); dwrong = not dok
        r["dose_ok"] += dok; r["wrong_dose"] += dwrong
        r["time_ok"] += norm(t["thoi_diem"]) == norm(p.get("Thời điểm", ""))
        if (not nok) or dwrong:
            r["serious"] += 1
            if not is_unsure(p):
                r["serious_silent"] += 1  # đọc SAI mà dòng đó KHÔNG bị gắn 'Chưa chắc chắn'
            bad.append(f"SAI: đáp án [{t['ten_thuoc']} | {t['lieu_luong']}] ≠ máy đọc [{p.get('Tên thuốc','')} | {p.get('Liều lượng','')}]")
    r["extra"] = len(preds) - len(used)
    r["_bad"] = bad
    return r


def evaluate(samples, truth, gate, predictor, sleep=0.0):
    """samples: [(đường_dẫn, id, điều_kiện)]. gate(img)->(severe, mild). predictor(img)->list thuốc."""
    from PIL import Image
    stats = defaultdict(lambda: defaultdict(int))
    detail = []
    stopped = None
    for path, id_, cond in samples:
        ckey = f"{cond}@{'tonghop' if id_.startswith('s') else 'that'}"  # tách đơn THẬT và đơn TỔNG HỢP
        if stopped:
            st = stats[ckey]; st["pending"] += 1
            detail.append([os.path.basename(path), cond, "CHƯA ĐO", stopped]); continue
        st = stats[ckey]; st["images"] += 1
        if id_ not in truth:
            detail.append([os.path.basename(path), cond, "BỎ QUA", "không có đáp án"]); st["images"] -= 1; continue
        img = Image.open(path)
        severe, mild = gate(img)
        if severe:
            st["blocked"] += 1; detail.append([os.path.basename(path), cond, "CHẶN", " ".join(severe)]); continue
        if mild:
            st["mild_flagged"] += 1
        try:
            preds = predictor(img, f"{os.path.basename(path)}:{os.path.getsize(path)}")
        except QuotaStop as e:
            st["images"] -= 1; st["pending"] += 1; stopped = str(e)
            detail.append([os.path.basename(path), cond, "CHƯA ĐO", stopped]); continue
        except Exception as e:
            st["errors"] += 1; detail.append([os.path.basename(path), cond, "LỖI API", str(e)[:120]]); continue
        # Mô phỏng ĐÚNG hành vi app (analyze_prescription_image + hàng chờ xác nhận):
        preds = [dict(x) for x in preds if isinstance(x, dict)]
        placeholders = [x for x in preds if not str(x.get("Tên thuốc", "")).strip()]  # dòng "ảnh có thể thiếu thuốc"
        preds = [x for x in preds if str(x.get("Tên thuốc", "")).strip()]
        if mild:  # app ép mọi dòng thành 'chưa chắc chắn' khi ảnh hơi mờ/thiếu sáng/chói
            for x in preds:
                x["Chưa chắc chắn"] = "có"
        # không đọc được thuốc nào -> app hiện cảnh báo "không nhận diện được", nên không phải lỗi im lặng
        any_flag = bool(placeholders) or not preds or any(is_unsure(x) for x in preds)
        r = score(truth[id_], preds, any_flag)
        bad = r.pop("_bad", [])
        for k, v in r.items():
            st[k] += int(v)
        detail.append([os.path.basename(path), cond, "OK", json.dumps(r, ensure_ascii=False) + (" || " + " ; ".join(bad) if bad else "")])
        if sleep:
            time.sleep(sleep)
    return stats, detail


def summary_md(stats):
    lines = ["| Điều kiện | Loại | Ảnh | Bị chặn | Lỗi API | Số thuốc | Tên hoạt chất đúng (CI95) | Hàm lượng đúng (CI95) | Bỏ sót | Sai tên/hàm lượng (nghiêm trọng) | **Sai KHÔNG cảnh báo** | **Bỏ sót KHÔNG cảnh báo** | Thừa |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    def kind(key):
        cond, src = key.rsplit("@", 1); real = src == "that"
        if cond.startswith("sim_"):
            return "mô phỏng từ ảnh thật" if real else "mô phỏng từ đơn tổng hợp"
        return "ảnh thật" if real else "đơn tổng hợp (bản gốc)"
    for key in sorted(stats, key=lambda k: (k.endswith("@tonghop"), k.startswith("sim_"), k)):
        s = stats[key]; n = s["n"]; cond = key.rsplit("@", 1)[0]
        if not (s["images"] or s["pending"]):
            continue
        lines.append(f"| {cond} | {kind(key)} | {s['images']} | {s['blocked']} | "
                     f"{s['errors']} | {n} | {fmt(s['name_ok'], n)} | {fmt(s['dose_ok'], n)} | {s['missed']} | "
                     f"{s['serious']} | {fmt(s['serious_silent'], n)} | {fmt(s['missed_silent'], n)} | {s['extra']} |")
    lines.append("")
    lines.append("> Cách chấm: *tên đúng* = đúng hoạt chất (bỏ biệt dược, hàm lượng, dạng bào chế; chấp nhận sai khác chính tả nhỏ, độ giống ≥ 88%); *hàm lượng đúng* = số và đơn vị khớp "
                 "(vd 500 mg = 500mg); *nghiêm trọng* = tìm thấy thuốc nhưng sai hoạt chất hoặc đưa ra hàm lượng KHÁC đáp án. "
                 "*KHÔNG cảnh báo* = lỗi mà người dùng không được nhắc (dòng không gắn 'Chưa chắc chắn' / ảnh không có cảnh báo thiếu thuốc): "
                 "đây là chỉ số an toàn chính, cần càng gần 0 càng tốt. Các CI coi mỗi dòng thuốc là độc lập nên hơi lạc quan.")
    pend = sum(stats[c]["pending"] for c in stats)
    if pend:
        lines.append("")
        lines.append(f"> **Chưa đo xong:** còn {pend} ảnh chưa được đo do hết hạn mức gọi API. "
                     "Số liệu trên chỉ gồm các ảnh đã đo; chạy lại cùng lệnh để đo tiếp (kết quả cũ được lấy từ cache).")
    return "\n".join(lines) + "\n"


def read_truth(path):
    t = defaultdict(list)
    for row in csv.DictReader(open(path, encoding="utf-8-sig")):
        if (row.get("id") or "").strip() and (row.get("ten_thuoc") or "").strip():
            t[row["id"].strip()].append(row)
    return t


def agreement(main_truth, blind_truth):
    """Độ đồng thuận về TÊN THUỐC giữa 2 người (Jaccard trên tập tên đã chuẩn hoá), chỉ trên các đơn cả hai cùng làm."""
    ids = [i for i in blind_truth if i in main_truth]
    if not ids:
        return None
    js = []
    for i in ids:
        a = {norm(r["ten_thuoc"]) for r in main_truth[i]}; b = {norm(r["ten_thuoc"]) for r in blind_truth[i]}
        js.append(len(a & b) / len(a | b) if a | b else 1.0)
    return len(ids), sum(js) / len(js)


def gemini_predictor(prompt, cache_path=None, max_calls=None):
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    cache = {}
    if cache_path and os.path.exists(cache_path):
        cache = json.load(open(cache_path, encoding="utf-8"))
    exhausted, calls = set(), [0]
    models = ("gemini-flash-latest", "gemini-flash-lite-latest")

    def save():
        if cache_path:
            os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
            json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)

    def run(img, key=None):
        if key and key in cache:
            return cache[key]
        if max_calls is not None and calls[0] >= max_calls:
            raise QuotaStop(f"đạt giới hạn --max-calls={max_calls}")
        last = None
        for model in models:
            if model in exhausted:
                continue
            for attempt in range(3):
                try:
                    calls[0] += 1
                    t = client.models.generate_content(model=model, contents=[img, prompt]).text
                    t = re.sub(r"^```json", "", t.strip(), flags=re.I).replace("```", "").strip()
                    m = re.search(r"\[.*\]", t, re.S)
                    out = json.loads(m.group(0) if m else t)
                    out = out if isinstance(out, list) else []
                    if key:
                        cache[key] = out; save()
                    return out
                except Exception as e:
                    last = e
                    msg = str(e).lower()
                    if "perday" in msg or "per day" in msg:  # hết hạn mức NGÀY: không thử lại, bỏ mô hình này
                        exhausted.add(model); break
                    if any(k in msg for k in ("503", "429", "unavailable", "quota", "exhausted")):
                        time.sleep(4 * (attempt + 1)); continue
                    break
        if all(m in exhausted for m in models):
            raise QuotaStop("hết hạn mức gọi Gemini trong ngày (gói miễn phí)")
        raise last
    return run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True); ap.add_argument("--images", required=True)
    ap.add_argument("--out", default="eval/results"); ap.add_argument("--blind")
    ap.add_argument("--sleep", type=float, default=2.0)
    ap.add_argument("--split", default=None, help="file split_dev.txt/split_test.txt (mỗi dòng 1 MÃ ĐƠN, vd s001): chỉ đo các đơn này")
    ap.add_argument("--max-calls", type=int, default=None, help="giới hạn số lần gọi API (để không vượt hạn mức)")
    ap.add_argument("--cache", default=None, help="file lưu kết quả đã đo (mặc định <out>/cache.json)")
    a = ap.parse_args()
    sys.path.insert(0, os.getcwd())
    from safepill_core import PRESCRIPTION_VISION_PROMPT, check_image_quality
    def gate(img):
        r = check_image_quality(img)
        return (r[0], r[1]) if isinstance(r, tuple) and len(r) == 2 else (r, [])
    truth = read_truth(a.truth)
    samples = []
    for f in sorted(os.listdir(a.images)):
        stem, ext = os.path.splitext(f)
        if ext.lower() in EXTS and "__" in stem:
            id_, cond = stem.split("__", 1)
            samples.append((os.path.join(a.images, f), id_, cond))
    if a.split:
        keep = {l.strip() for l in open(a.split, encoding="utf-8") if l.strip()}
        samples = [x for x in samples if x[1] in keep]
        print(f"Chỉ đo {len(keep)} đơn trong {a.split}: {len(samples)} ảnh")
    # Đơn THẬT trước, rồi đơn tổng hợp; mỗi đơn đo trọn các điều kiện trước khi sang đơn khác
    samples.sort(key=lambda x: (x[1].startswith("s"), x[1], x[2].startswith("sim_"), x[2]))
    cache_path = a.cache or os.path.join(a.out, "cache.json")
    stats, detail = evaluate(samples, truth, gate,
                             gemini_predictor(PRESCRIPTION_VISION_PROMPT, cache_path, a.max_calls), a.sleep)
    os.makedirs(a.out, exist_ok=True)
    md = summary_md(stats)
    if a.blind:
        ag = agreement(truth, read_truth(a.blind))
        md += (f"\nĐộ đồng thuận tên thuốc giữa 2 người dán nhãn: {100 * ag[1]:.0f}% trên {ag[0]} đơn\n" if ag
               else "\nChưa có đơn nào được cả 2 người dán nhãn\n")
    open(os.path.join(a.out, "summary.md"), "w", encoding="utf-8").write(md)
    with open(os.path.join(a.out, "detail.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        csv.writer(fh).writerows([["file", "condition", "status", "info"]] + detail)
    print(md)


if __name__ == "__main__":
    main()
