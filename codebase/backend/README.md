# Backend

FastAPI backend của VLearn Smart Contextual Companion. Pipeline nhận câu hỏi,
phân loại intent/scope, truy xuất slide hoặc transcript, rồi quyết định trả lời,
hỏi lại, từ chối hoặc đề xuất chuyển TA.

## Chạy

Từ root repo:

```powershell
python -m venv codebase\backend\.venv
codebase\backend\.venv\Scripts\python.exe -m pip install -r codebase\backend\requirements.txt
Copy-Item codebase\backend\.env.example codebase\backend\.env
cd codebase\backend
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Không có key, hệ thống vẫn chạy các nhánh rule/mock. Để dùng model thật, cấu
hình `NVIDIA_API_KEY`; tìm nguồn ngoài cần `TAVILY_API_KEY`; gửi TA cần Telegram
hoặc webhook trong `.env`.

## Pipeline

```text
question + UI context
        |
        v
intent/scope routing
        |
        v
scope-aware retrieval (PDF + transcript)
        |
        +--> clarify / refuse / TA handoff
        |
        v
grounded answer + citation validation + trace
```

Các điểm vào chính:

- `api.py`: FastAPI endpoints.
- `companion/scope.py`: intent/scope và safety routing.
- `companion/retriever.py`: index và truy xuất học liệu.
- `companion/answer.py`: sinh câu trả lời grounded.
- `companion/tavily_search.py`: kiến thức ngoài khi được phép.
- `companion/ta_notifier.py`: Telegram/webhook TA.
- `runs/`: trace sinh khi chạy, bị gitignore.

Data mặc định được đọc từ `codebase/data/vlearn-pack/`; có thể override bằng
`VLEARN_SLIDES_DIR`, `VLEARN_TRANSCRIPT_DIR` hoặc `VLEARN_TRANSCRIPT_PATH`.

## Test và eval

```powershell
cd codebase\backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe eval_golden_set.py --version v3 --transport api
```

Golden set và kết quả được lưu ở root [`../../eval/`](../../eval/). Không sửa
case của một version đã phát hành để chạy theo implementation; thay đổi kỳ vọng
phải tạo version kế tiếp và ghi rõ lý do.
