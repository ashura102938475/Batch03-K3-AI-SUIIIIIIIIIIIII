# Agent Context

Đọc các file theo thứ tự:

1. `README.md`: cấu trúc bài nộp, thành viên, lệnh chạy và trạng thái.
2. `spec.md`: nguồn chính thức cho bài toán, AI decision, scope và quality bar.
3. `codebase/docs/agent-context-vlearn-smart-contextual-companion.md`: product context chi tiết.
4. `eval/README.md` và `eval/golden_set_v3.json`: quy tắc đánh giá.

## Mục tiêu

VLearn Smart Contextual Companion cải thiện phản hồi của VLearn Tutor bằng cách:

- nhận diện đúng phạm vi selected text/current page/document/session;
- truy xuất và trích dẫn đúng học liệu;
- tách kiến thức ngoài khỏi nội dung môn học;
- hỏi lại hoặc chuyển TA khi thiếu căn cứ/độ tin cậy thấp.

AI decision phải đo được là: câu hỏi được trả lời từ nguồn chính thức, cần nguồn
ngoài, cần hỏi lại hay cần chuyển TA. Không mô tả chung chung là “AI sinh câu
trả lời”.

## Guardrails khi sửa

- Không thay đổi golden set đã phát hành để khớp code; tạo version mới.
- Không tuyên bố chất lượng cao hơn kết quả lưu trong `eval/`.
- Không bịa feedback, quote, tên người dùng hoặc reflection cá nhân.
- Không commit API key trong `codebase/backend/.env`.
- Không mở rộng thành full LMS, Discord bot hoặc hệ thống chấm bài.
- Mỗi thay đổi routing/grounding cần có regression test tương ứng.

## Trạng thái hiện tại

- Prototype: React/Vite + FastAPI, PDF thật từ data pack.
- Model mặc định: `nvidia/nemotron-3-nano-30b-a3b`.
- Golden set v3: 31 case; báo cáo lưu gần nhất 16/31, 6 critical failures.
- Validation: chưa có bằng chứng thật (`0/5`).
- Demo slide: bản nháp 6 trang, chưa được coi là final khi validation chưa đủ.
