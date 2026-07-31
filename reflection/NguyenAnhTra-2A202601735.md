# Reflection - Nguyễn Anh Trà

- **Mã học viên:** `2A202601735`
- **Họ tên:** Nguyễn Anh Trà
- **GitHub:** `ashura102938475`
- **Phụ trách chính:** Backend API (`api.py`), Provider/Model Architecture (`providers/`), Tích hợp luồng Chuyển TA (TA Handoff Integration), Hybrid Classifier & Safety Guardrails, Golden Set Evaluator (`eval/`).

---

## Dấu vết commit (Kiểm chứng qua `git log`)

| Commit / PR | Thời điểm | Nội dung thực hiện |
|---|---|---|
| `107ecee` | 31/07 12:34 | `feat(routing)`: Triển khai Classifier lai (Hybrid) + Cổng an toàn cứng (Safety Guardrails), triệt tiêu 7 lỗi Critical về 0 |
| `12de84a` | 31/07 13:00 | Merge PR #14 (`feat/scope-routing-hybrid-classifier`): Đưa classifier lai vào pipeline chính |
| `52e55fd` | 31/07 14:20 | `fix(answer,routing)`: Nâng cấp chất lượng câu trả lời chi tiết và xử lý các ca lỗi khi test câu dài |
| `1749802` | 31/07 04:00 | `fix`: Điều chỉnh nút làm rõ phạm vi gửi lại đúng câu hỏi gốc kèm scope đã làm rõ |
| `ee3f424` | 31/07 05:15 | `fix`: Tối ưu hóa thuật toán định tuyến tìm kiếm nguồn web ngoài (`should_try_external`) |
| `bc2d8f7` | 31/07 17:00 | Merge PR #15: Tích hợp tài liệu reflection và rà soát chất lượng bài nộp |

---

## 1. Phần tôi trực tiếp làm và có thể giải thích

Tôi đóng vai trò **Backend & AI Architecture Lead**, chịu trách nhiệm trực tiếp thiết kế API RESTful, tích hợp các mô hình LLM, xây dựng cơ chế phân loại phạm vi lai (Hybrid Scope Classifier) và cổng an toàn (Safety Guardrails), cùng luồng chuyển tiếp hỗ trợ cho Trợ giảng (TA Handoff).

### A. FastAPI Backend Service & Chuẩn hoá API Contract (`codebase/backend/api.py`)
- Xây dựng FastAPI application phục vụ toàn bộ ứng dụng Tutor. Chuẩn hóa contract giao tiếp giữa Frontend và Backend bao gồm: `/health`, `/api/chat`, `/api/scope/detect`, `/api/ta/handoff`.
- Thiết kế payload trả về chứa minh bạch đầy đủ thông tin: `answer`, `scope`, `confidence`, `sources` (citations), `suggested_actions` (scope clarification), `ta_handoff_suggested`, và `ta_draft_ticket`.

### B. Kiến trúc Provider & Model Pipeline (`codebase/backend/providers/`)
- Thiết kế lớp trừu tượng `BaseProvider` hỗ trợ kết nối linh hoạt với nhiều nhà cung cấp AI: NVIDIA NIM (`nvidia/nemotron-3-nano-30b-a3b` cho grounded answer generation và `google/gemma-3-1b-it` cho classifier fast-tier), OpenAI, Gemini, Anthropic.
- Tích hợp cơ chế fallback tự động: Khi mô hình sinh câu trả lời bị lỗi quota hoặc mạng, hệ thống tự động fallback mượt mà về rule-based guardrail mà không làm crash server hay làm gián đoạn trải nghiệm học viên.

### C. Bộ phân loại phạm vi Lai (Hybrid Scope Classifier - `companion/classify.py`) & Cổng an toàn (Safety Guardrails - `companion/safety.py`)
- Kết hợp điểm mạnh của hai phương pháp: **Rule-based deterministic engine** (nhanh, rẻ, chính xác $100\%$ cho các mẫu chuẩn) và **Fast 1B Model Classifier** (`google/gemma-3-1b-it`) cho các ca ngôn ngữ tự nhiên phức tạp.
- Phát triển cổng an toàn cứng (`safety.py`) ở cuối pipeline: Đảm bảo bất kỳ câu hỏi nào rơi vào nhóm từ chối (`out_of_scope`, `prohibited_assessment`, `prompt_attack`) đều **tuyệt đối không được mang citation**, triệt hạ triệt để nguy cơ AI bịa đặt căn cứ hay làm hộ bài thi.

### D. Luồng chuyển hỗ trợ TA (TA Handoff Integration)
- Xây dựng module `should_suggest_ta` tại `companion/routing.py` để làm "Single Source of Truth" cho quyết định khi nào hiển thị nút "Chuyển TA".
- Tự động đóng gói `ta_draft_ticket` bao gồm: Tiêu đề câu hỏi, Context trang/buổi học hiện tại, Lý do chuyển TA, và bản nháp câu hỏi đã chuẩn hoá để học viên gửi trực tiếp cho Trợ giảng chỉ bằng một cú nhấp.

---

## 2. AI đã hỗ trợ tôi như thế nào và cách tôi kiểm chứng

Tôi sử dụng AI Agent để hỗ trợ tái cấu trúc code (refactoring), viết unit tests và hỗ trợ phân tích nguyên nhân gốc (root cause analysis) từ log kiểm thử Golden Set.

**Cách tôi kiểm chứng độc lập:**
1. **Kiểm thử qua Benchmark Golden Set v3:** 
   - Tôi bắt buộc mọi nâng cấp về backend phải chạy qua toàn bộ 31 test cases của Golden Set v3 (`eval_golden_set.py`).
   - Đợt nâng cấp Classifier lai và Guardrail cứng ngày 31/07 đã được kiểm chứng bằng số liệu cụ thể: Tỷ lệ pass đạt **25/31 (80.65%)** (vượt chỉ tiêu 75%), độ chính xác nhận diện Scope đạt **100.0%**, và số lỗi Critical bị kéo từ **7 lỗi xuống đúng 0 lỗi**.
2. **Kiểm chứng tính toàn vẹn của API via Pytest:**
   - Xây dựng và duy trì 92 unit tests bao phủ các module `test_companion.py`, `test_classify.py`, `test_safety.py`, và `test_api_citations.py`.
   - Đảm bảo 100% test pass xanh trước khi merge bất kỳ PR nào vào nhánh `develop`.
3. **Thử nghiệm thủ công với các edge cases:**
   - Tự tay test các câu hỏi dài, câu cố tình viết sai chính tả ("dealine nộp lab"), câu hỏi dồn nhiều mệnh đề để kiểm tra xem hệ thống có bị lừa gán sai scope hay không.

---

## 3. Sự cố / Failure khiến tôi thay đổi quyết định

**Sự cố:**
Ở các phiên bản trước, báo cáo eval ghi nhận 6 lỗi Critical do mô hình tự ý sinh câu trả lời kèm trích dẫn `[Trang 3]` cho các câu hỏi vi phạm như: xin đáp án bài kiểm tra, hỏi deadline sai chính tả, hoặc yêu cầu mật khẩu hệ thống. Lý do là vì parser rule ở tầng đầu bị lọt từ khóa, dẫn đến câu hỏi rơi xuống nhánh sinh câu trả lời mặc định, và LLM tự tin bịa ra citation.

**Quyết định thay đổi:**
- **Không đặt niềm tin tuyệt đối vào một cổng duy nhất ở đầu pipeline:** Trước đây tôi nghĩ chỉ cần cải thiện prompt hoặc viết thêm từ khóa ở `detect_intent`. Nhưng thực tế cho thấy không danh sách từ khóa nào phủ hết được ngôn ngữ người dùng.
- **Thêm cổng bảo mật 2 lớp (Defense-in-depth):** Tôi bổ sung `companion/safety.py` nằm ở **cuối pipeline**, ngay trước khi trả API về cho client. Nếu phát hiện intent là từ chối hoặc vi phạm quy định, cổng này sẽ ghi đè loại bỏ toàn bộ citation chips và ép trả về mẫu từ chối an toàn kèm nút Chuyển TA. Quyết định này giúp đưa số lỗi Critical về **0** tuyệt đối.

---

## 4. Nếu có thêm một tuần, tôi sẽ ưu tiên điều gì

1. **Ưu tiên 1 — Tối ưu hóa Latency (Live P90 Latency < 12s):**
   - Hiện tại P90 latency đang ở mức ~18.5 giây khi đọc toàn bộ tài liệu (`current_document`). Tôi sẽ triển khai kỹ thuật Reranking (dùng mô hình Cohere hoặc Cross-Encoder nhỏ) kết hợp cap dynamic chunking để giảm token đầu vào cho LLM, kéo P90 latency xuống dưới 10 giây.
2. **Ưu tiên 2 — Nâng cấp thuật toán Semantic Retrieval (Hybrid Search BM25 + Dense Embedding):**
   - Hiện tại `retriever.py` dùng thuật toán khớp từ trùng cơ bản. Nếu có thêm 1 tuần, tôi sẽ tích hợp ChromaDB / FAISS với BGE-m3 embedding để nâng tỷ lệ Citation Grounding từ **70.59% lên trên 90%**.
3. **Ưu tiên 3 — Xây dựng Dashboard theo dõi Trace & Analytics thời gian thực:**
   - Triển khai màn hình Admin Dashboard cho phép TA và giảng viên xem lại các câu hỏi bị chuyển TA (`ta_draft_ticket`), phân tích các chủ đề học viên hay vướng mắc nhất trong buổi học để kịp thời điều chỉnh bài giảng.
