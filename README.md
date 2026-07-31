# VLearn Smart Contextual Companion

Trợ lý học tập theo ngữ cảnh cho VLearn. Sản phẩm nhận diện phạm vi câu hỏi
(trang hiện tại, tài liệu, buổi học hoặc nguồn ngoài), truy xuất học liệu liên
quan, trả lời kèm citation và đề xuất chuyển TA khi thiếu căn cứ hoặc vượt phạm vi.

## Thành viên và phân công

Bảng dưới đây tổng hợp theo lịch sử commit. Nhóm cần điền mã học viên và xác nhận
họ tên trước khi nộp.

| Mã HV | Họ tên | GitHub | Phần phụ trách |
|---|---|---|---|
| Cần bổ sung | Cần xác nhận | `ashura102938475` | Backend API, provider/model, tích hợp TA |
| Cần bổ sung | Cần xác nhận | `Hieunc2910` | Phân tích dữ liệu, golden set/evaluator, grounding |
| Cần bổ sung | Cần xác nhận | `codecuatai` | Frontend, PDF reader, chat/citation UX |
| Cần bổ sung | Bùi Gia Uy | `BuiGiaUy` | Prototype ban đầu, setup và tài liệu |

## Cấu trúc bài nộp

```text
repo/
├── README.md          # Thành viên, phân công, hướng dẫn chạy
├── spec.md            # AI Spec theo template của khóa
├── demo-slides.pdf    # Bản nháp slide demo 6 trang
├── codebase/          # Prototype và tài liệu kỹ thuật
├── eval/              # Golden set và kết quả các lượt chạy
├── validation/        # Feedback log từ user test
└── reflection/        # Mỗi thành viên một file reflection
```

Chi tiết phần nào chạy thật và phần nào mock nằm tại
[`codebase/README.md`](codebase/README.md).

## AI quyết định gì?

**AI quyết định câu hỏi có thể trả lời từ học liệu chính thức, cần bổ sung nguồn
ngoài, cần hỏi lại hay phải chuyển TA; câu trả lời grounded được sinh bằng
`nvidia/nemotron-3-nano-30b-a3b`, với `google/gemma-3-1b-it` là classifier tùy
chọn và luật deterministic làm fallback.**

## Chạy prototype

Yêu cầu: Python 3.10+, Node.js 20+ và npm. Chạy các lệnh từ root repo.

```powershell
python -m venv codebase\backend\.venv
codebase\backend\.venv\Scripts\python.exe -m pip install -r codebase\backend\requirements.txt
Copy-Item codebase\backend\.env.example codebase\backend\.env
```

Điền ít nhất `NVIDIA_API_KEY` vào `codebase/backend/.env`, rồi chạy backend:

```powershell
cd codebase\backend
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Trong terminal khác:

```powershell
cd codebase\frontend
npm ci
npm run dev
```

Mở `http://127.0.0.1:5174`. Kiểm tra backend tại
`http://127.0.0.1:8000/health`.

## Kiểm thử

```powershell
cd codebase\backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe eval_golden_set.py --version v3 --transport api
```

Golden set v3 có **31 câu**, trong đó **10 câu bắt nguồn từ quan sát thực tế**.
Lượt chạy được lưu gần nhất đạt **16/31 (51,61%)** và còn **6 lỗi critical**.
Chuẩn cam kết là tối thiểu **75% tổng thể** và **không có lỗi critical** về bịa
claim/citation, trả lời hộ bài đánh giá hoặc bịa thông tin logistics. Xem đầy đủ
tại [`eval/EVAL_REPORT_V3.md`](eval/EVAL_REPORT_V3.md).

## Trạng thái bài nộp

- `spec.md`: đã có AI Spec và bằng chứng data mining.
- `demo-slides.pdf`: bản nháp 6 trang; slide validation còn chờ dữ liệu thật.
- `eval/`: đã có golden set v2/v3, kết quả và manual review.
- `validation/`: biểu mẫu đã sẵn sàng, hiện chưa có đủ 5 user test.
- `reflection/`: đã tạo file theo contributor; mỗi thành viên phải tự hoàn thiện.
- Trước khi nộp cần bổ sung mã HV, xác nhận họ tên, ít nhất 5 feedback thật và
  reflection cá nhân.

## Bảo mật

Không commit `codebase/backend/.env` hoặc API key. Data pack đã ẩn danh chỉ được
dùng trong phạm vi hackathon; khi trích dẫn chatlog, dùng `turn_id` thay vì cố
suy ngược danh tính.
