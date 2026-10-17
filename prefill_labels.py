"""Điền sẵn đáp án bằng Gemini cho các ảnh rõ nét, để người dán nhãn chỉ việc SỬA trong bảng tính.

    export GEMINI_API_KEY="..."
    python tools/prefill_labels.py eval/images eval/labels_draft.csv

Chỉ đọc ảnh <mã>__ro_net.*. Mở labels_draft.csv bằng Excel/Numbers/Google Sheets, đối chiếu từng dòng
với ẢNH GỐC, sửa/xoá/thêm dòng, rồi lưu thành eval/labels.csv (giữ cột id, ten_thuoc, lieu_luong, thoi_diem).
Cột can_nguoi_2 = x : đơn được chọn ngẫu nhiên (25%) để NGƯỜI THỨ HAI dán nhãn độc lập, không xem kết quả AI.
Mẫu cho người thứ hai: eval/labels_blind_template.csv
"""
import csv, json, os, random, re, sys, time

KEEP = ["id", "ten_thuoc", "lieu_luong", "thoi_diem", "ghi_chu", "anh_goc", "can_nguoi_2"]


def parse_json_array(text):
    t = re.sub(r"^```json", "", text.strip(), flags=re.I).replace("```", "").strip()
    m = re.search(r"\[.*\]", t, re.S)
    return json.loads(m.group(0) if m else t)


def load_prompt():
    sys.path.insert(0, os.getcwd())
    from safepill_core import PRESCRIPTION_VISION_PROMPT
    return PRESCRIPTION_VISION_PROMPT


def call_gemini(client, img, prompt):
    last = None
    for model in ("gemini-flash-latest", "gemini-flash-lite-latest"):
        for attempt in range(3):
            try:
                r = client.models.generate_content(model=model, contents=[img, prompt])
                return parse_json_array(r.text)
            except Exception as e:  # thử lại khi quá tải / giới hạn tốc độ
                last = e
                if any(k in str(e).lower() for k in ("503", "429", "unavailable", "quota", "exhausted")):
                    time.sleep(4 * (attempt + 1))
                    continue
                break
    raise last


def main(images_dir, out_csv, seed=7, fraction=0.25, sleep=2.0):
    from PIL import Image
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = load_prompt()
    files = sorted(f for f in os.listdir(images_dir) if "__ro_net." in f)
    ids = [f.split("__")[0] for f in files]
    rnd = random.Random(seed)
    second = set(rnd.sample(ids, max(1, round(len(ids) * fraction)))) if ids else set()
    rows = []
    for f, i in zip(files, ids):
        try:
            meds = call_gemini(client, Image.open(os.path.join(images_dir, f)), prompt) or [{}]
            note = ""
        except Exception as e:
            meds, note = [{}], f"LỖI GEMINI: {str(e)[:80]} - tự điền tay"
        for m in meds:
            rows.append({"id": i, "ten_thuoc": m.get("Tên thuốc", ""), "lieu_luong": m.get("Liều lượng", ""),
                         "thoi_diem": m.get("Thời điểm", ""), "ghi_chu": note, "anh_goc": f,
                         "can_nguoi_2": "x" if i in second else ""})
        print(f"{f}: {len(meds)} thuốc")
        time.sleep(sleep)
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=KEEP); w.writeheader(); w.writerows(rows)
    blind = os.path.join(os.path.dirname(out_csv) or ".", "labels_blind_template.csv")
    with open(blind, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(["id", "ten_thuoc", "lieu_luong", "thoi_diem", "anh_goc"])
        for f, i in zip(files, ids):
            if i in second:
                w.writerow([i, "", "", "", f])
    print(f"Đã ghi {out_csv} ({len(rows)} dòng) và {blind} ({len(second)} đơn cho người thứ hai)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
