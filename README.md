# VLearn Smart Contextual Companion

Prototype trợ lý học tập theo ngữ cảnh cho VLearn. Ứng dụng cho phép học viên hỏi về slide, tài liệu hoặc buổi học hiện tại; backend nhận diện intent/scope, truy xuất ngữ cảnh liên quan, rồi trả lời có citation hoặc chuyển hướng TA khi thiếu chắc chắn.

Repo này có 2 phần chính:

- `backend/`: FastAPI API, Streamlit prototype, pipeline AI/retrieval/eval.
- `frontend/`: giao diện React chạy bằng Vite, gọi API tại `http://localhost:8000`.

## Yêu cầu cài đặt

Cài sẵn:

- Python 3.10+
- Node.js 20+
- npm

Các lệnh bên dưới giả định bạn đang dùng PowerShell tại thư mục gốc của repo.

## Cấu trúc thư mục

```text
backend/
  api.py                 # FastAPI backend cho frontend
  app.py                 # Streamlit prototype
  companion/             # intent, scope, retrieval, answer, trace
  providers/             # wrapper các LLM provider
  corpus/                # corpus fallback khi sample data không khả dụng
  eval/                  # golden set và kết quả đánh giá
frontend/
  src/App.jsx            # UI chính
  src/data/slides.js     # metadata tài liệu và demo prompts cho UI
data/                    # data course được cấp, không commit ra ngoài
docs/, spec.md           # tài liệu sản phẩm và AI spec
```

## Setup backend

Tạo virtual environment và cài dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Nếu chưa có API key, backend vẫn chạy ở mock mode.

Muốn dùng LLM thật, mở `backend/.env` và điền một provider:

```env
DEFAULT_PROVIDER=nvidia
NVIDIA_API_KEY=your_key_here
```

Các provider hỗ trợ: `nvidia`, `gemini`, `openai`, `openrouter`, `anthropic`.

## Chạy backend API

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Kiểm tra backend:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Kỳ vọng nhận được `status: online`. Nếu `active_provider` là `MOCK`, nghĩa là chưa có API key hợp lệ.

## Chạy frontend

Mở terminal mới tại thư mục gốc:

```powershell
cd frontend
npm ci
npm run dev
```

Mở URL Vite hiển thị trong terminal, thường là:

```text
http://127.0.0.1:5173
```

Frontend đang hard-code API base là `http://localhost:8000`, nên cần chạy backend trước.

## Chạy Streamlit prototype

Nếu muốn xem prototype cũ:

```powershell
cd backend
..\.venv\Scripts\streamlit.exe run app.py
```

Mở:

```text
http://localhost:8501
```

## Chạy đánh giá backend

Golden set nằm tại `backend/eval/golden_set.json`.

```powershell
cd backend
..\.venv\Scripts\python.exe eval_golden_set.py
```

Khi sửa logic trong `companion/`, hãy cập nhật golden set hoặc báo cáo trong `backend/eval/` nếu hành vi kỳ vọng thay đổi.

## Lưu ý dữ liệu và bảo mật

- Không commit API key trong `backend/.env`.
- Không chia sẻ hoặc commit raw data trong `data/`.
- Trace sinh ra trong `backend/runs/*.json`; chỉ force-add file mẫu khi cần nộp bằng chứng.
- `VLEARN_TRANSCRIPT_PATH` trong `.env` có thể dùng để trỏ tới transcript thật nếu đường dẫn mặc định không đúng.

## Lỗi thường gặp

**Port 8000 đã được dùng**

```powershell
netstat -ano | Select-String ':8000'
Stop-Process -Id <PID>
```

**pip đọc `requirements.txt` lỗi encoding trên Windows**

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

**Frontend không gọi được API**

Kiểm tra backend còn chạy không:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```
