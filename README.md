# Mô phỏng hệ thống SCADA/PLC với Mã hóa AES

## Mô tả

Dự án bao gồm hai thành phần chính:

1.  **`server_OpenPLC.py`**: Đóng vai trò là một **PLC (Programmable Logic Controller)**. Nó chạy một logic điều khiển (mô phỏng theo ngôn ngữ ST - Structured Text) để vận hành một hệ thống giả định (bơm, van, tuabin) và giám sát dòng điện.
2.  **`client_HMI.py`**: Đóng vai trò là **HMI (Human-Machine Interface)**. Đây là giao diện cho phép người vận hành gửi các lệnh điều khiển (`START`, `STOP`) đến PLC và nhận dữ liệu trạng thái để giám sát.

**Mục tiêu chính**: Nhóm muốn triển khai và kiểm chứng một giải pháp mã hóa AES-256 nhằm bảo mật kênh truyền thông tin liên lạc giữa HMI (Client) và PLC (Server) trong một hệ thống SCADA mô phỏng, đảm bảo tính bí mật và toàn vẹn của dữ liệu điều khiển.

## Tính năng chính

* **Mô hình Client-Server**: Mô phỏng rõ ràng sự tương tác giữa HMI (Client) và PLC (Server).
* **Mã hóa AES-256**: Toàn bộ dữ liệu truyền đi (cả lệnh từ HMI và trạng thái từ PLC) đều được mã hóa bằng `pycryptodome`.
* **Mô phỏng Logic PLC**: Server chạy một vòng lặp logic (scan cycle) 1 giây/lần, mô phỏng hoạt động của một PLC thực tế với các bộ `TON` (Timer On-Delay).
* **Xử lý Đa luồng (Multi-threading)**: Cả server và client đều sử dụng `threading` để xử lý việc gửi/nhận và logic nghiệp vụ một cách đồng thời, không bị "treo" (blocking).
* **Logic Chốt lỗi (Fault Latching)**: Hệ thống mô phỏng một tính năng an toàn quan trọng: khi bị `Overload` (quá tải), hệ thống sẽ tự động dừng và **không** tự khởi động lại cho đến khi người vận hành nhấn `START` lần nữa.
* **Giao tiếp Tối ưu**: Server chỉ gửi cập nhật trạng thái về HMI khi dữ liệu thực sự thay đổi, tránh làm "lụt" (flood) mạng.

## Cài đặt và Chạy thử

### 1. Yêu cầu

* Python 3.6+

### 2. Cài đặt

1.  Clone repository này về máy:
    ```bash
    git clone [URL-GITHUB-CUA-BAN]
    cd [TEN-THU-MUC-DU-AN]
    ```

2.  Cài đặt các thư viện cần thiết:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Chạy Demo

Bạn sẽ cần mở 2 cửa sổ terminal (hoặc 2 tab trong VS Code).

**Tại Terminal 1 (Chạy Server/PLC):**

```bash
python server_OpenPLC.py

**Tại Terminal 2 (Chạy Client/HMI):**

```bash
python client_HMI.py