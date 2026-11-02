# Nail Mockup Generator – MVP

MVP local: giữ cố định ảnh bàn tay `assets/base_hand.png`, thay 5 móng bằng 5 mẫu được tách từ ảnh thiết kế. Không gọi API tạo ảnh, không watermark.

## 1. Yêu cầu
- Python 3.10 hoặc 3.11
- macOS / Windows / Linux
- 4 GB RAM trở lên để chạy thử; ảnh lớn có thể cần thêm RAM.

## 2. Cài đặt trên macOS (M2) / Linux

```bash
cd nail-mockup-generator
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Mở URL hiện trong terminal, thường là http://localhost:8501.

## 3. Windows

```powershell
py -3.11 -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## 4. Cách sử dụng
1. Mở ứng dụng.
2. Upload ảnh thiết kế nail có nền sáng.
3. Kiểm tra các mẫu được tách.
4. Chọn mẫu tương ứng cho 5 ngón tay.
5. Bấm `Tạo mockup`.
6. Tải ảnh PNG.

## 5. Hiệu chỉnh vị trí móng trên ảnh base
Các tọa độ 4 góc của từng móng nằm trong `config.json` → `nail_targets` → `quad`.

Mỗi `quad` gồm 4 điểm theo thứ tự:
- top-left
- top-right
- bottom-right
- bottom-left

Tọa độ đang được đặt làm cấu hình khởi tạo theo ảnh base đính kèm (1024x1024). Cần kiểm tra và tinh chỉnh trên ảnh thực tế trước khi chạy hàng loạt. Có thể dùng công cụ annotate polygon bất kỳ để lấy tọa độ pixel.

## 6. Giới hạn của MVP hiện tại
- Tách mẫu bằng computer vision dựa trên nền sáng; ảnh nền phức tạp hoặc bóng đổ dính vào nhau có thể cần crop/segment thủ công.
- Warp hiện tại là perspective warp, chưa phải mô hình 3D/TPS. Móng có góc chụp khác nhiều so với base có thể bị méo.
- Cấu hình 5 vùng móng của base là tọa độ cố định và cần hiệu chỉnh một lần.
- Bộ compositing bảo toàn một phần độ sáng của ảnh base; chưa thể khôi phục hoàn hảo highlight/specular reflection.
- Bản này là POC để kiểm tra pipeline, chưa nên dùng tự động xuất 1.000 ảnh trước khi kiểm duyệt chất lượng và hiệu chỉnh template.

## 7. Cấu trúc
```
nail-mockup-generator/
  app.py
  engine.py
  config.json
  requirements.txt
  assets/
    base_hand.png
    sample_nail_design.png
  outputs/
```

## 8. Chạy bằng ảnh mẫu
Mở app và upload `assets/sample_nail_design.png`.
