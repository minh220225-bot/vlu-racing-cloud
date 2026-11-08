# 🏎️ VLU Racing Cloud - Trung Tâm Xe Đua & RGB LED Studio

Hệ thống Web Server trên Render Cloud phục vụ giám sát Telemetry, cân bằng IMU máy bay/drone và phối màu hiệu ứng 6 Cụm LED WS2812B cho Xe Đua RC XIAO ESP32-S3.

## 🚀 Triển khai trên Render Cloud
1. Vào [dashboard.render.com](https://dashboard.render.com)
2. Bấm **New +** -> **Web Service**
3. Chọn Repository `vlu-racing-cloud` (hoặc `minh220225-bot/vlu-racing-cloud`)
4. Cấu hình tự động theo `render.yaml`:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Bấm **Create Web Service**!

## 🌐 Các Đường Dẫn Chính
- `/` hoặc `/xedua`: Dashboard Giám sát Góc Nghiêng IMU 3D, Gia Tốc G, Vận Tốc, Nhảy Bay
- `/xedua/led`: Studio Phối Màu Xi Nhan Động & Đèn Gầm Cyberpunk
- `/api/xedua/sync`: Giao thức đồng bộ ngầm thời gian thực 2 chiều với FreeRTOS Core 0 trên ESP32-S3
- `/api/firmware/latest.bin`: Tải bản firmware mới nhất phục vụ Cloud OTA
