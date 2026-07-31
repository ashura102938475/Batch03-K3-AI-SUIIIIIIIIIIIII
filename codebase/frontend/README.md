# Frontend Setup Guide

Frontend của VLearn Smart Contextual Companion là ứng dụng React chạy bằng Vite. UI render PDF học liệu thật, hỗ trợ chọn văn bản, chat theo ngữ cảnh, citation và luồng chuyển TA. Ứng dụng gọi backend FastAPI tại `http://localhost:8000`.

## Yêu cầu

- Node.js 20+
- npm
- Backend đang chạy ở `http://127.0.0.1:8000`

Kiểm tra backend:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Nếu backend trả về `status: online`, frontend có thể gọi API.

## Cài dependency

Từ thư mục gốc repo:

```powershell
cd codebase\frontend
npm ci
```

Dùng `npm ci` để cài đúng theo `package-lock.json`. Nếu chưa có lockfile mới hoặc đang phát triển package, có thể dùng `npm install`.

## Chạy development server

```powershell
npm run dev
```

Vite sẽ chạy trên:

```text
http://127.0.0.1:5173
```

Nếu cổng `5173` bận, Vite có thể chọn cổng tiếp theo. Xem URL chính xác trong terminal.

## Build production

```powershell
npm run build
```

Kết quả build nằm trong `codebase/frontend/dist/`.

Xem thử bản build:

```powershell
npm run preview
```

## Cấu trúc chính

```text
codebase/frontend/
  index.html
  package.json
  vite.config.js
  src/
    main.jsx          # React entrypoint
    App.jsx           # UI và logic gọi API
    styles.css        # style toàn app
    data/slides.js    # metadata tài liệu và demo prompts hiển thị trong UI
```

## API backend đang dùng

Trong `src/App.jsx`:

```js
const API_BASE_URL = "http://localhost:8000";
```

Các endpoint chính:

- `POST /api/v1/companion/chat`: gửi câu hỏi và nhận câu trả lời có ngữ cảnh.
- `POST /api/v1/escalate-ta`: tạo yêu cầu chuyển TA.

Nếu đổi port backend, cần cập nhật `API_BASE_URL`.

## Lỗi thường gặp

**Frontend báo không gọi được API**

- Đảm bảo backend đang chạy cổng `8000`.
- Mở `http://127.0.0.1:8000/health` để kiểm tra.
- Kiểm tra terminal backend có lỗi provider hoặc env không.

**Thiếu package hoặc Vite không chạy**

```powershell
npm ci
npm run dev
```

**Port 5173 bị bận**

Vite thường tự đổi cổng. Nếu muốn kiểm tra process đang dùng cổng:

```powershell
netstat -ano | Select-String ':5173'
```
