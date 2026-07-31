# Prototype

`codebase/` chứa toàn bộ phần chạy được của VLearn Smart Contextual Companion,
data pack được cấp và tài liệu kỹ thuật hỗ trợ.

## Thành phần

```text
codebase/
├── backend/            # FastAPI, retrieval, routing, model provider, tests
├── frontend/           # React/Vite, PDF reader và chat sidebar
├── data/vlearn-pack/   # 2 PDF, 6 transcript và chatlog đã ẩn danh
├── docs/               # Phân tích dữ liệu, product context, API spec
├── reference/          # Đề bài, guide, template và rubric gốc
└── reference-assets/   # Tài liệu JTBD tham khảo
```

## Phần chạy thật và phần mock

| Thành phần | Trạng thái |
|---|---|
| Hiển thị 2 PDF mẫu và điều hướng trang | Thật, dùng file trong `codebase/data/` |
| Nhận diện intent/scope | Thật, classifier tùy chọn + luật fallback |
| Retrieval slide và transcript | Thật, index 751 chunks khi data pack khả dụng |
| Sinh câu trả lời | Thật khi có API key; mặc định NVIDIA Nemotron |
| Kiểm tra citation và trace | Thật |
| Tìm nguồn ngoài | Thật khi cấu hình `TAVILY_API_KEY` |
| Gửi yêu cầu sang Telegram/webhook TA | Thật khi cấu hình endpoint/token |
| Vỏ VLearn, course/day navigation và quota | Mock, không kết nối VLearn production |
| Đăng nhập, quyền lớp học và lưu lịch sử dài hạn | Chưa triển khai |
| Provider fallback không có key | Mock/rule response, được ghi rõ trong trace |

## Điểm vào

- Backend API: `codebase/backend/api.py`
- Pipeline: `codebase/backend/companion/`
- Frontend: `codebase/frontend/src/App.jsx`
- Golden set và kết quả: `eval/`
- AI Spec: `spec.md`

Xem lệnh cài đặt và chạy ở [`../README.md`](../README.md).
