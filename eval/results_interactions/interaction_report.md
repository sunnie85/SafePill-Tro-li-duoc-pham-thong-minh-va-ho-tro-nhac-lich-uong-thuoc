# Kết quả tương tác thuốc
_38 cặp (28 có tương tác, 10 không). Khoảng tin cậy Wilson 95%._

## Chỉ số chính (chỉ tính cặp độc lập, KHÔNG tính nhóm `trong_csdl` vì CSDL được dựng từ đó)

- **Recall tổng thể:** 0/20 = 0% (CI 0–16%)
- **Recall trong phạm vi** (cả hai thuốc được nhận diện): 0/7 = 0% (CI 0–35%)
- Không nhận diện (hệ thống phải báo 'chưa kiểm tra được'): 13/20 = 65% (CI 43–82%)
- **Bỏ sót im lặng** (thuốc nhận diện nhưng cặp không có, hệ thống nói 'không thấy cảnh báo'): 7/20 = 35% (CI 18–57%)
- Báo nhầm trên cặp không tương tác: 0/10 = 0% (CI 0–28%)
- Độ phủ: 16/34 thuốc trong bộ gold được nhận diện (47%)

## Nhóm `trong_csdl` (kiểm tra hồi quy, kết quả hiển nhiên cao)

- Phát hiện: 8/8 = 100% (CI 68–100%)

## Chi tiết từng cặp

| Thuốc A | Thuốc B | Đáp án | Nhóm | Hệ thống | Đánh giá | Đã xác nhận nguồn |
|---|---|---|---|---|---|---|
| Aspirin | Ibuprofen | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Aspirin | Warfarin | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Warfarin | Amiodarone | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Digoxin | Furosemide | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Simvastatin | Amiodarone | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Losartan | Spironolactone | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Clopidogrel | Omeprazole | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Metformin | Cimetidine | yes | trong_csdl | PHÁT HIỆN | đúng | chưa |
| Warfarin | Clarithromycin | yes | thuoc_co_trong_csdl_cap_chua_co | IM LẶNG | **BỎ SÓT IM LẶNG** | chưa |
| Clopidogrel | Warfarin | yes | thuoc_co_trong_csdl_cap_chua_co | IM LẶNG | **BỎ SÓT IM LẶNG** | chưa |
| Digoxin | Spironolactone | yes | thuoc_co_trong_csdl_cap_chua_co | IM LẶNG | **BỎ SÓT IM LẶNG** | chưa |
| Digoxin | Clarithromycin | yes | thuoc_co_trong_csdl_cap_chua_co | IM LẶNG | **BỎ SÓT IM LẶNG** | chưa |
| Ibuprofen | Spironolactone | yes | thuoc_co_trong_csdl_cap_chua_co | IM LẶNG | **BỎ SÓT IM LẶNG** | chưa |
| Enalapril | Spironolactone | yes | thuoc_co_trong_csdl_cap_chua_co | IM LẶNG | **BỎ SÓT IM LẶNG** | chưa |
| Aspirin | Furosemide | yes | thuoc_co_trong_csdl_cap_chua_co | IM LẶNG | **BỎ SÓT IM LẶNG** | chưa |
| Warfarin | Fluconazole | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Warfarin | Ciprofloxacin | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Simvastatin | Amlodipine | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Atorvastatin | Clarithromycin | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Ibuprofen | Prednisolone | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Methotrexate | Trimethoprim | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Aspirin | Methotrexate | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Sildenafil | Nitroglycerin | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Tramadol | Fluoxetine | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Ciprofloxacin | Calcium carbonate | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Levothyroxine | Calcium carbonate | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Lisinopril | Spironolactone | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Spironolactone | Potassium chloride | yes | ngoai_csdl | KHÔNG NHẬN DIỆN | bỏ sót nhưng phải báo 'chưa kiểm tra được' | chưa |
| Paracetamol | Omeprazole | no | am_tinh | IM LẶNG | đúng | chưa |
| Paracetamol | Amoxicillin | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |
| Paracetamol | Cetirizine | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |
| Omeprazole | Cetirizine | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |
| Amlodipine | Losartan | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |
| Paracetamol | Loratadine | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |
| Amoxicillin | Omeprazole | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |
| Atorvastatin | Paracetamol | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |
| Metformin | Losartan | no | am_tinh | IM LẶNG | đúng | chưa |
| Amoxicillin | Aspirin | no | am_tinh | KHÔNG NHẬN DIỆN | đúng | chưa |

> **Chưa xác nhận nguồn:** 38/38 cặp. Phải tra từng cặp trên Drugs.com (hoặc Dược thư) và điền cột `da_xac_nhan` trước khi báo cáo.
> Mẫu nhỏ, khoảng tin cậy rộng; 'không có tương tác' nghĩa là không ghi nhận mức vừa/nặng theo nguồn, không phải bảo đảm an toàn.