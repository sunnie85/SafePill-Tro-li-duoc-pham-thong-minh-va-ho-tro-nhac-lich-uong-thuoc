# Nhật ký thay đổi (CHANGELOG)

Định dạng: mỗi phiên bản liệt kê *Thêm mới*, *Thay đổi*, *Sửa lỗi* và *Hạn chế còn lại*.

## [1.1-safety] – 2026-10-17

Phiên bản cải tiến theo góp ý của Ban giám khảo: bộ đánh giá rõ ràng hơn, kiểm tra ảnh và xác minh trước khi lưu, cảnh báo khi thiếu căn cứ.

### Thêm mới
- **Cổng kiểm tra chất lượng ảnh trước OCR** (`check_image_quality`): chặn ảnh mờ, quá tối, độ phân giải thấp (cạnh ngắn dưới 600 px); cảnh báo (không chặn) khi ảnh chói.
- **Bảng xác minh bắt buộc trước khi lưu**: hiển thị ảnh gốc cạnh bảng, cột "Chưa chắc chắn", ô xác nhận; nút Lưu bị khoá khi có dòng thiếu tên thuốc hoặc liều.
- **Cảnh báo tương tác thuốc tách trạng thái**: *có tương tác* / *không ghi nhận trong dữ liệu hiện có* / *chưa kiểm tra được vì thuốc chưa nhận diện*; ghi chú "không thấy cảnh báo không có nghĩa là an toàn" ở tab Tủ thuốc.
- **Cảnh báo độ tin cậy ở tab Tư vấn AI**: chấm độ tin cậy câu trả lời, biểu ngữ cảnh báo khi thiếu nguồn uy tín, quy tắc an toàn trong prompt, lọc nguồn theo tên miền.
- **Chuỗi dự phòng khi Gemini quá tải**: `gemini-flash-latest` → `gemini-flash-lite-latest` → OCR offline OpenVINO (luôn đánh dấu "không chắc chắn", kèm cảnh báo dễ bỏ sót thuốc).
- **Chuẩn hoá tên thuốc**: bỏ dấu, tách hàm lượng và dạng bào chế, ánh xạ biệt dược sang hoạt chất, gợi ý "Ý bạn là...?" thay vì tự thay.
- **Bộ công cụ đánh giá** (`tools/`):
  - `make_variants.py`: tạo ảnh mô phỏng mờ, tối, chói, cắt chữ (tiền tố `sim_`).
  - `gen_synthetic_rx.py`: sinh đơn tổng hợp có đáp án chính xác, tên bệnh nhân giả.
  - `prefill_labels.py`: điền sẵn nhãn nháp bằng Gemini để người dán nhãn đối chiếu và sửa.
  - `eval_pipeline.py`: chấm theo hoạt chất và hàm lượng, khoảng tin cậy 95% (Wilson), tách riêng ảnh thật / mô phỏng / tổng hợp, lưu bộ nhớ đệm để chấm lại không tốn lượt gọi API, dừng sớm khi hết hạn mức.
  - `eval_interactions.py` + `interaction_gold.csv`: đo cảnh báo tương tác trên 38 cặp thuốc.
- Kiểm thử `tests/test_core_safety.py`.
- Tài liệu: `docs/DATASHEET.md`, `docs/evaluation_report.md`, `docs/PROMPT_LOG.md`, `docs/evidence/`.

### Thay đổi
- File safepill_update.py thay thế safepill_old.py (cải tiến)
- Tách logic an toàn sang `safepill_core.py` (không phụ thuộc Streamlit nên kiểm thử và đánh giá được); `safepill_update.py` import từ core. Dữ liệu và hàm tương tác chỉ còn **một nguồn** trong core (trước đó được sao chép ở cả hai file).
- Cách chấm OCR: so theo hoạt chất và hàm lượng đã tách (không so từng ký tự); lỗi nghiêm trọng = tìm thấy thuốc nhưng sai hoạt chất hoặc đưa ra hàm lượng khác đáp án.

### Sửa lỗi
- Trang Streamlit trắng khi thiếu `face_recognition_models`: bắt `BaseException` (thư viện gọi `quit()` ném `SystemExit`), bổ sung phụ thuộc vào `requirements.txt`.
- Khi ảnh tải lên bị chặn, người dùng gần như không thấy thông báo; đã hiển thị rõ lý do.
- Bỏ `from urllib import response` thừa; bỏ khoá dịch trùng; thêm khoá dịch `matrix_footer_caption` còn thiếu.
- `NameError` do gọi `check_image_quality` sai vị trí.

### Hạn chế còn lại
- Dữ liệu tương tác hẹp: kiểm tra trên 38 cặp, phát hiện đúng 0/20 cặp có tương tác, độ phủ 47% (xem README).
- Bộ ảnh thật còn nhỏ; ảnh tổng hợp và ảnh mô phỏng dễ hơn ảnh chụp thật.
- Cảnh báo "ảnh bị chói" có thể xuất hiện với ảnh nền trắng (chỉ là cảnh báo nhẹ, không chặn).
- Mã PIN băm SHA-256 không có muối; nhật ký rà soát OCR băm số điện thoại có thể dò ngược.
- Tab Tư vấn AI chưa có dự phòng mô hình.

## [1.0] – `[05/8/2026]`
Phiên bản đầu: nhắc thuốc, đọc đơn thuốc bằng Gemini, tủ thuốc, kiểm tra tương tác cơ bản, hỏi đáp AI.
