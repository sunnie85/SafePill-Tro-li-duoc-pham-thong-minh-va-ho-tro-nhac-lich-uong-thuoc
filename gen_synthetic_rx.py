"""Tạo đơn thuốc TỔNG HỢP (do máy vẽ) kèm đáp án chính xác tuyệt đối, để mở rộng quy mô thử nghiệm.

    python gen_synthetic_rx.py eval/clear_synth eval/labels_synth.csv 40

- Tên thuốc/hàm lượng/giờ uống được CHỌN TRƯỚC rồi mới vẽ lên ảnh, nên đáp án đúng 100%, không cần dán nhãn tay,
  không có thông tin cá nhân. Tên bệnh nhân là tên giả rõ ràng ("NGUYEN VAN MAU").
- Có 3 kiểu trình bày, đổi cỡ chữ, nền giấy, nghiêng nhẹ, nhiễu hạt -> đa dạng hơn một mẫu duy nhất.
- Ảnh tổng hợp phải được BÁO CÁO RIÊNG là "đơn tổng hợp" (mã đơn bắt đầu bằng 's'), không gộp với đơn thật.

Sau khi chạy:
    python make_variants.py eval/clear_synth eval/images        # sinh biến thể mờ/tối/chói/cắt
    tail -n +2 eval/labels_synth.csv >> eval/labels.csv          # gộp nhãn (labels.csv phải có sẵn dòng tiêu đề)
"""
import csv, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]
FONTS_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# (tên thuốc, hàm lượng, dạng, số lượng gợi ý)
DRUGS = [
    ("Paracetamol", "500mg", "viên"), ("Amoxicillin", "500mg", "viên"), ("Cefuroxim", "500mg", "viên"),
    ("Ibuprofen", "400mg", "viên"), ("Loratadin", "10mg", "viên"), ("Omeprazol", "20mg", "viên"),
    ("Metformin", "500mg", "viên"), ("Amlodipin", "5mg", "viên"), ("Atorvastatin", "20mg", "viên"),
    ("Cetirizin", "10mg", "viên"), ("Azithromycin", "250mg", "viên"), ("Prednisolon", "5mg", "viên"),
    ("Domperidon", "10mg", "viên"), ("Diclofenac", "50mg", "viên"), ("Losartan", "50mg", "viên"),
    ("Bisoprolol", "5mg", "viên"), ("Glimepirid", "2mg", "viên"), ("Simvastatin", "20mg", "viên"),
    ("Ambroxol", "30mg", "viên"), ("Acetylcystein", "200mg", "gói"), ("Levofloxacin", "500mg", "viên"),
    ("Clarithromycin", "500mg", "viên"), ("Aspirin", "81mg", "viên"), ("Warfarin", "5mg", "viên"),
    ("Salbutamol", "2mg", "viên"), ("Vitamin C", "500mg", "viên"), ("Esomeprazol", "40mg", "viên"),
    ("Furosemid", "40mg", "viên"), ("Spironolacton", "25mg", "viên"), ("Clopidogrel", "75mg", "viên"),
]
WHEN = [("sáng", "Sáng 1 viên"), ("chiều", "Chiều 1 viên"), ("sáng, tối", "Sáng 1 viên, tối 1 viên"),
        ("sáng, chiều, tối", "Ngày 3 lần, mỗi lần 1 viên"), ("tối", "Tối 1 viên trước khi ngủ"),
        ("sáng", "Uống sáng sau ăn"), ("sáng, tối", "Ngày 2 lần sau ăn")]
CLINICS = ["PHONG KHAM DA KHOA MAU", "TRAM Y TE MAU", "BENH VIEN MAU (DU LIEU TONG HOP)"]


def font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def render(rng, items, idx):
    W = rng.choice([1200, 1400, 1600])
    base = rng.choice([20, 22, 24]) * W // 1400
    f, fb = font(FONTS, base * 2), font(FONTS_BOLD, base * 2)
    fh = font(FONTS_BOLD, int(base * 2.6))
    style = rng.choice(["bang", "danh_sach", "gon"])
    row_h = int(base * (4.2 if style == "bang" else 3.6))
    H = max(1000, int(base * 14 + row_h * len(items)))
    tint = rng.choice([(255, 255, 255), (252, 250, 240), (245, 248, 252)])
    img = Image.new("RGB", (W, H), tint)
    d = ImageDraw.Draw(img)
    y = base * 2
    d.text((W // 2, y), rng.choice(CLINICS), font=fb, fill=(30, 30, 30), anchor="mt")
    y += base * 3
    d.text((W // 2, y), "DON THUOC" if rng.random() < .3 else "ĐƠN THUỐC", font=fh, fill=(0, 0, 0), anchor="mt")
    y += base * 4
    d.text((base * 3, y), f"Họ tên: NGUYEN VAN MAU    Tuổi: {rng.randint(8, 80)}    Mã: TH{idx:04d}", font=f, fill=(20, 20, 20))
    y += base * 3
    d.line((base * 3, y, W - base * 3, y), fill=(120, 120, 120), width=2)
    y += base
    for n, it in enumerate(items, 1):
        name, dose, form, qty, when_txt = it
        if style == "bang":
            d.text((base * 3, y), f"{n}", font=f, fill=(0, 0, 0))
            d.text((base * 6, y), f"{name} {dose}", font=fb, fill=(0, 0, 0))
            d.text((W - base * 12, y), f"SL: {qty} {form}", font=f, fill=(0, 0, 0))
            d.text((base * 6, y + base * 2), when_txt, font=f, fill=(60, 60, 60))
        elif style == "danh_sach":
            d.text((base * 3, y), f"{n}. {name} {dose} - {qty} {form}", font=fb, fill=(0, 0, 0))
            d.text((base * 5, y + base * 2), f"Cách dùng: {when_txt}", font=f, fill=(60, 60, 60))
        else:
            d.text((base * 3, y), f"{n}) {name} {dose} ({qty} {form}): {when_txt}", font=f, fill=(0, 0, 0))
        y += row_h
    d.text((base * 3, y + base), "Lời dặn: uống thuốc sau ăn, tái khám sau 7 ngày.", font=f, fill=(40, 40, 40))
    # nghiêng nhẹ + nhiễu hạt để gần ảnh chụp hơn
    img = img.rotate(rng.uniform(-1.5, 1.5), expand=True, fillcolor=tint, resample=Image.BICUBIC)
    arr = np.asarray(img, dtype=np.float32)
    arr += np.random.default_rng(idx).normal(0, 4, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def main(out_dir, out_csv, n):
    rng = random.Random(20261017)
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for i in range(1, n + 1):
        k = rng.randint(2, 6)
        picks = rng.sample(DRUGS, k)
        items = []
        for name, dose, form in picks:
            when_key, when_txt = rng.choice(WHEN)
            qty = rng.choice([10, 14, 20, 28, 30])
            items.append((name, dose, form, qty, when_txt))
            rows.append({"id": f"s{i:03d}", "ten_thuoc": name, "lieu_luong": dose, "thoi_diem": when_key,
                         "ghi_chu": "tổng hợp", "anh_goc": f"s{i:03d}", "can_nguoi_2": ""})
        render(rng, items, i).save(os.path.join(out_dir, f"s{i:03d}.jpg"), quality=95)
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "ten_thuoc", "lieu_luong", "thoi_diem", "ghi_chu", "anh_goc", "can_nguoi_2"])
        w.writeheader()
        w.writerows(rows)
    print(f"Đã tạo {n} đơn tổng hợp trong {out_dir} và {len(rows)} dòng nhãn trong {out_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
