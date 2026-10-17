# SafePill-Trợ lí dược phẩm thông minh và hỗ trợ nhắc lịch uống thuốc

SafePill là ứng dụng Streamlit giúp người dùng đọc đơn thuốc từ ảnh, lập lịch nhắc uống thuốc, kiểm tra tương tác thuốc và hỏi đáp có kiểm soát độ tin cậy.

> **Lưu ý y tế:** SafePill chỉ hỗ trợ nhắc nhở và tra cứu, **không thay thế bác sĩ hoặc dược sĩ**. Việc không thấy cảnh báo **không có nghĩa là an toàn**.

## Tính năng chính
- Đọc đơn thuốc từ ảnh (Gemini), có dự phòng OCR offline (OpenVINO).
- Lịch nhắc uống thuốc, tủ thuốc, hồ sơ người dùng (Supabase).
- Kiểm tra tương tác thuốc với các trạng thái tách biệt: *có tương tác* / *không ghi nhận trong dữ liệu hiện có* / *chưa kiểm tra được vì thuốc chưa nhận diện*.
- Tab tư vấn AI có chấm độ tin cậy và cảnh báo khi thiếu nguồn uy tín.

## Cải tiến theo góp ý của Ban giám khảo

| Góp ý | Đã làm | Mã nguồn | Minh chứng |
|---|---|---|---|
| Bộ đánh giá rõ ràng, đa dạng, quy mô lớn hơn | Bộ ảnh gồm đơn thật, ảnh mô phỏng (mờ, tối, chói, cắt chữ) và đơn tổng hợp có đáp án chính xác; công cụ đo tách riêng từng nhóm, có khoảng tin cậy 95%; bộ 38 cặp thuốc để đo cảnh báo tương tác | `tools/`, `eval/`, `docs/DATASHEET.md` | `docs/evaluation_report.md`, `eval/results/summary.md` |
| Thử OCR với ảnh thiếu chữ, mờ, tối; bắt xác minh trước khi lưu | Cổng chất lượng ảnh (mờ, tối, chói, độ phân giải); bảng xác minh có ảnh gốc, cột "Chưa chắc chắn"; không lưu được khi thiếu tên thuốc hoặc liều | `safepill_core.py` (`check_image_quality`, `validate_pending_rows`) | `docs/evidence/`, `tests/test_core_safety.py` |
| Cảnh báo khi thiếu căn cứ hoặc độ tin cậy thấp | Phân biệt "không ghi nhận" với "chưa kiểm tra được"; biểu ngữ độ tin cậy ở tab tư vấn; quy tắc an toàn trong prompt; lọc nguồn theo tên miền | `safepill_core.py` (`pair_check_status`, `interaction_coverage_note`, `assess_answer_confidence`, `SAFETY_PROMPT_RULES`) | `docs/evidence/` |

Chi tiết thay đổi: [CHANGELOG.md](CHANGELOG.md). Nhật ký sử dụng AI: [docs/PROMPT_LOG.md](docs/PROMPT_LOG.md).

## Cài đặt và chạy

```bash
git clone <URL-repo>
cd <thư-mục-repo>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

1. **Khoá API:** sao chép `appsettings/appsettings.example.json` thành `appsettings/appsettings.json` và điền khoá của bạn (Gemini, Supabase). File này nằm trong `.gitignore`; **không bao giờ commit khoá thật**.
2. **OCR offline (tuỳ chọn):** tải model OpenVINO vào `models/` (không đưa lên repo vì dung lượng lớn):
   `[dán các lệnh tải horizontal-text-detection-0001 và text-recognition-0014]`
3. Chạy ứng dụng:
   ```bash
   streamlit run safepill_update.py
   ```

## Kiểm thử và đánh giá

```bash
python -m pytest tests/                                                # logic an toàn
python tools/make_variants.py eval/clear eval/images                   # ảnh mô phỏng (mờ, tối, chói, cắt)
python tools/gen_synthetic_rx.py eval/clear_synth eval/labels_synth.csv 40   # đơn tổng hợp
export GEMINI_API_KEY="..."                                            # khoá của bạn, không ghi vào mã nguồn
python tools/eval_pipeline.py --truth eval/labels.csv --images eval/images --out eval/results
python tools/eval_interactions.py                                      # [bổ sung tham số nếu có] đo cảnh báo tương tác
```

Cách chấm OCR: *tên đúng* = đúng hoạt chất; *hàm lượng đúng* = số và đơn vị khớp; *nghiêm trọng* = tìm thấy thuốc nhưng sai hoạt chất hoặc đưa ra hàm lượng khác đáp án. Ảnh bị cổng chất lượng chặn được báo riêng, không tính là đọc sai. Kết quả **ảnh thật**, **mô phỏng** và **tổng hợp** luôn được tách riêng. Kết quả thô của mô hình được lưu để chấm lại mà không gọi lại API.

## Kết quả đánh giá

### Đọc đơn thuốc (OCR)
Trên 40 đơn tổng hợp và 2 đơn thật qua được cổng chất lượng, không có lỗi nghiêm trọng (176 thuốc), ở cả ảnh gốc và ảnh mô phỏng cắt, chói, tối. Cổng chất lượng chặn 45/45 ảnh mờ mô phỏng. Một số ảnh thật bị chặn vì độ phân giải thấp (`[số]`/5).

`[Dán bảng từ eval/results/summary.md sau khi chạy với nhãn đã đối chiếu tay]`

**Cần đọc kèm, kết quả này chưa chứng minh được độ chính xác với ảnh chụp khó ngoài đời thực:**
- Đơn tổng hợp có chữ in sạch và danh mục thuốc cố định, dễ hơn ảnh thật; ảnh "tối" mô phỏng chỉ là giảm độ sáng, dễ hơn ảnh thiếu sáng thật có nhiễu và mờ.
- Ảnh mô phỏng cắt, chói, tối cho kết quả gần như giống ảnh gốc, tức là chưa đủ khó.
- Số đơn thật được đo rất ít, nên con số về ảnh thật chưa có ý nghĩa thống kê.
- Trường "thời điểm uống" đọc kém hơn tên thuốc và hàm lượng (khoảng 18/48 ở ảnh gốc trong một lần đo trước), vì vậy luôn nằm trong bảng xác minh.

### Cảnh báo tương tác thuốc
Đo trên bộ 38 cặp thuốc (`eval/interaction_gold.csv`):

| Chỉ số | Kết quả |
|---|---|
| Phát hiện đúng cặp có tương tác (recall) | 0/20 |
| Bỏ sót im lặng (hệ thống nhận diện thuốc nhưng không có dữ liệu cặp) | 7/20 |
| Không nhận diện được thuốc (hệ thống báo "chưa kiểm tra được") | 13/20 |
| Báo nhầm khi không có tương tác | 0/10 |
| Độ phủ dữ liệu | 47% |

**Đây là hạn chế lớn nhất của sản phẩm hiện tại.** Dữ liệu tương tác mới bao phủ một số ít hoạt chất, chưa có nhiều thuốc phổ biến (ví dụ Amoxicillin). Vì vậy hệ thống chủ yếu trả lời "chưa kiểm tra được" hoặc "không ghi nhận", và luôn kèm cảnh báo rằng điều đó **không có nghĩa là an toàn**. Không dùng kết quả này để quyết định dùng thuốc.

## Giới hạn đã biết

- Bộ ảnh thật còn nhỏ; chưa có đánh giá của dược sĩ độc lập. Kế hoạch: mở rộng bộ ảnh thật với sự tham gia của dược sĩ hoặc cơ sở y tế.
- Dữ liệu tương tác hẹp (xem bảng trên), chưa theo từng cặp một cách đầy đủ, chưa có nguồn và ngày cập nhật cho từng mục. Cần chuyển sang dữ liệu theo cặp có nguồn tham khảo uy tín và được dược sĩ rà soát.
- Ảnh có cạnh ngắn dưới 600 px bị từ chối; ảnh nền trắng có thể nhận cảnh báo "chói" không cần thiết.
- OCR offline (OpenVINO) không có dấu tiếng Việt và thường bỏ sót thuốc; kết quả luôn được đánh dấu "không chắc chắn".
- Tab tư vấn AI chỉ dùng một mô hình, chưa có dự phòng khi quá tải.
- Mã PIN hiện lưu bằng băm SHA-256 không có muối (kèm tương thích ngược bản cũ); cần nâng cấp trước khi dùng thực tế.
- Nhật ký rà soát OCR (`db/ocr_review_log.sql`): số điện thoại được băm nhưng có thể dò ngược; cần ẩn danh mạnh hơn, giới hạn quyền ghi và thông báo cho người dùng trước khi bật.
- Gói API miễn phí giới hạn số lượt gọi mỗi ngày, ảnh hưởng quy mô đánh giá.
- `safepill_update.py` (giao diện) và `safepill_core.py` (logic) là hai file bổ trợ nhau, không phải một file hợp nhất: app import các hàm an toàn từ core. Giao diện cần được chạy và kiểm tra bằng tay sau mỗi lần sửa.

## Cấu trúc thư mục

```
safepill_orc.py.        https://docs.google.com/document/d/1Ocw3Qajnonzrn5l7Dyts_5ikMp20mOSrGT8LMxw9OOI/edit?usp=sharing (code trước cải tiến)
safepill_update.py      Ứng dụng Streamlit (giao diện, Supabase, gọi Gemini)
safepill_core.py        Logic thuần, không phụ thuộc Streamlit: kiểm tra ảnh, xác minh, độ tin cậy, dữ liệu và hàm tương tác
openvino_ocr_helper.py  OCR offline dự phòng
tests/                  Kiểm thử logic an toàn
tools/                  Tạo dữ liệu và đánh giá
eval/                   Nhãn đáp án, bộ cặp thuốc, kết quả (không chứa ảnh đơn thuốc thật)
db/                     Cấu trúc bảng cơ sở dữ liệu
docs/                   Báo cáo đánh giá, datasheet, prompt log, minh chứng
```

## Dữ liệu và quyền riêng tư

Repo **không chứa** ảnh đơn thuốc thật hay thông tin cá nhân. Đơn tổng hợp dùng tên bệnh nhân giả. Khoá API và cấu hình thật không được đưa lên repo.
