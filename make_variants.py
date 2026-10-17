"""Tạo ảnh mô phỏng (mờ, tối, chói, cắt chữ) từ ảnh đơn thuốc rõ nét.

    python tools/make_variants.py eval/clear eval/images

Đặt ảnh rõ nét vào eval/clear/ với tên <mã_đơn>.jpg (ví dụ don01.jpg, don02.png).
Kết quả trong eval/images/ (tên file = <mã_đơn>__<điều_kiện>.jpg):
    don01__ro_net.jpg                (bản gốc rõ nét)
    don01__sim_mo.jpg / sim_toi / sim_choi / sim_cat   (ảnh MÔ PHỎNG)
Ảnh chụp THẬT ở điều kiện xấu: tự đặt tên don01__mo.jpg, don01__thieu_sang.jpg... rồi bỏ vào eval/images/.
Ảnh mô phỏng được báo cáo riêng (điều kiện bắt đầu bằng "sim_") vì chỉ gần đúng ảnh thật.
"""
import os, sys
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

EXTS = (".jpg", ".jpeg", ".png", ".webp")


def blur(img):
    return img.filter(ImageFilter.GaussianBlur(radius=max(img.size) / 250))


def dark(img):
    return ImageEnhance.Brightness(img).enhance(0.3)


def glare(img):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.55, h * 0.4
    mask = np.exp(-(((xx - cx) / (w * 0.35)) ** 2 + ((yy - cy) / (h * 0.3)) ** 2))[..., None] * 0.95
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    return Image.fromarray((arr * (1 - mask) + 255 * mask).astype(np.uint8))


def crop(img):
    w, h = img.size
    return img.crop((0, 0, int(w * 0.62), h))  # cắt mất gần 40% bên phải, mất chữ ở mép


VARIANTS = {"sim_mo": blur, "sim_toi": dark, "sim_choi": glare, "sim_cat": crop}


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(src)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in EXTS:
            continue
        img = Image.open(os.path.join(src, name)).convert("RGB")
        img.save(os.path.join(dst, f"{stem}__ro_net.jpg"), quality=95)
        for cond, fn in VARIANTS.items():
            fn(img).save(os.path.join(dst, f"{stem}__{cond}.jpg"), quality=90)
        n += 1
    print(f"Đã xử lý {n} ảnh gốc -> {n * (1 + len(VARIANTS))} ảnh trong {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
