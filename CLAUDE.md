# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo này là gì

Đây **không phải codebase** — là repo sự kiện Mini Hackathon AI Batch 03 (K3), gồm 3 lớp:

1. **Luật chơi (root, do ban tổ chức phát)** — `01-de-bai.md` (đề bài + 5 tiêu chí nghiệm thu) · `02-guide.md` (5 giai đoạn) · `03-template-ai-spec.md` (khung `spec.md`) · `04-rubric.md` (100 điểm + checklist 6 mốc)
2. **Tài liệu nhóm** — `docs/` (đề tài đang theo)
3. **Data pack thật đã ẩn danh** — `data/vlearn-pack/`

Deliverable trung tâm là `spec.md` — **chưa có trên `main`** (branch `docs` đang có một bản đang viết dở), cùng với `eval/`, `validation/`, `reflection/`. Prototype thì đã có: `frontend/` và `codebase/`.

**Không có build system, test runner, lint hay `package.json`.** Công việc thực tế: viết markdown + script Python ad-hoc (pandas) đọc CSV chatlog. Không có command chuẩn để chạy — tạo script trong scratchpad hoặc `eval/` khi cần.

## Đề tài nhóm: VLearn Smart Contextual Companion

Cải thiện VLearn Tutor bằng **scope-aware retrieval + citation-first response + conditional TA handoff**. Không phải "làm chatbot thông minh hơn nói chung".

**Lát cắt MỘT CÂU:** Học viên đang ôn lại trên VLearn hỏi về một slide/tài liệu/buổi học, hệ thống nhận diện đúng phạm vi context cần đọc, truy xuất slide liên quan và trả lời có citation hoặc chuyển TA khi độ tin cậy thấp.

**Solution flow:** detect intent (summary/explain/logistics/out-of-scope/prompt attack) → detect scope → retrieve theo scope → generate grounded response có citation → low-confidence/out-of-scope thì hỏi lại, từ chối hữu ích, hoặc chuyển TA.

**4 scope là trục xương sống** — mọi prompt, eval case và UI phải phân biệt được: `selected text` · `current page` · `current document` · `whole session`.

**Automation: conditional.** AI tự trả lời khi có căn cứ + citation đủ tin cậy; thiếu dữ liệu / scope mơ hồ / vượt phạm vi thì hỏi lại hoặc chuyển TA. Lý do theo cost-of-error: trả lời sai làm học viên học sai kiến thức.

Non-goals: `docs/agent-context-vlearn-smart-contextual-companion.md` §9. Đừng mở rộng scope ra Discord bot, full LMS, hay sửa mọi loại câu hỏi của tutor.

## Con số evidence đã chốt — dùng lại, đừng tính lại

Đã mining trong `docs/data-analysis-vlearn-context.md` §5 (nền: 1.261 lượt hỏi-đáp, 369 user, 585 conversation):

| Số | Ý nghĩa |
|---|---|
| `156/1.261` (12,4%) | lượt có nhu cầu summary/tổng hợp/ý chính/keyword/note |
| `62` | lượt summary ở phạm vi rộng (toàn bài / toàn buổi / file / slide day) |
| `87/156` (55,8%) | lượt summary gặp phản hồi "không tìm thấy / không truy cập được / rất tiếc" |
| `101/156` (64,7%) | lượt summary không có citation |
| `582/1.261` (46,2%) | tổng thể tutor trả lời citation rỗng |
| `16/155` (10,3%) | summary có trang trong prompt mà cite đúng trang context (`100/155` không cite gì) |

Evidence turn IDs dùng để trích: broad summary fail `T0408` `T1164` `T0213` `T0345` · local summary fail `T0649` `T0523` · citation lệch `T0520` `T1108` `T0399` · out-of-scope/handoff `T0707` `T1027` `T0794` `T0582`.

Nếu tính ra số khác: **ghi lại phương pháp đếm mới**, đừng thay số âm thầm — R1 chấm "phương pháp đếm kiểm lại được".

## Làm việc với data pack

### Ràng buộc bảo mật (bắt buộc — xem `README.md` §"Bảo mật dữ liệu được cung cấp")

- **Không commit nguyên data pack vào repo nộp bài.** Trích ngắn vài dòng để minh hoạ.
- Golden set và evidence ghi `turn_id` / mã transcript `[Txx-NNN]`, không dán nguyên văn dài.
- Đưa data ra công cụ AI ngoài: chỉ phần tối thiểu cần thiết — free tier có thể dùng data để train.
- Không suy ngược danh tính từ mã `U/C/T/M` hay nhãn `[học viên]`.
- Không commit API key — dùng biến môi trường (`.gitignore` đã chặn `*.env`).

### Bẫy schema chatlog (`data/vlearn-pack/chatlog/DATA_DICTIONARY.md`)

- **1 turn = đúng 2 dòng** (`role` = `student` + `tutor`), join bằng `turn_id`. 2.522 dòng = 1.261 turn.
- `content` của student có prefix metadata `(Trang N, đoạn được chọn: "...")` rồi mới tới câu hỏi thật. **Phải tách phần sau metadata trước khi đếm intent** — không thì số bị phóng đại vì đoạn bôi đen cũng bị đếm.
- Tiếng Việt phải normalize (lowercase + bỏ dấu) trước khi match keyword: `tóm tắt` → `tom tat`.
- `total_cost_usd` **luôn = 0** — cost tracking hỏng, đừng phân tích chi phí từ cột này.
- `misconceptions` và `follow_ups` **luôn `[]`** (0/1.261) — field chưa từng được dùng.
- `rating` chỉ có ~2,8% dòng → tín hiệu phụ, không dùng làm bằng chứng chính.
- `conversation_mode` 100% `in_class`, `turn_status` 100% `completed` → không lọc được gì.
- `day_code` = `New learning material` chiếm 794 msg — có thể là bug đặt tên, không phải một buổi học thật.
- `avg_latency_ms`: median 1.758ms, p90 3.686ms, max 23.848ms (có outlier ~24s).

### Transcript (`data/vlearn-pack/transcript/`)

~700 đoạn có mã trích dẫn `[Txx-NNN]`; chỗ ASR không khôi phục được đánh dấu `[không nghe rõ]`. Bảng ánh xạ 6 file → buổi học nằm trong `transcript/README.md` — **định vị buổi là suy đoán từ nội dung** và có cột độ tin cậy (2 file không gắn được số ngày). Đừng khẳng định chắc "đây là Day N".

## Cấu trúc nộp bài & bản đồ điểm

```
spec.md · demo-slides.pdf · codebase/ · eval/ · validation/ · reflection/
```

Trên `main` mới có `codebase/` (và `frontend/`); `spec.md`, `eval/`, `validation/`, `reflection/` còn thiếu. **Mỗi con điểm trỏ về một file** — trước khi làm việc gì, xác định nó rơi vào file nào:

| Khối | Điểm | File |
|---|---|---|
| R1 · Bằng chứng & impact | 15 | `spec.md` §1-§2 + log khảo sát/mining |
| R2 · Lát cắt & thiết kế | 15 | `spec.md` §4 |
| R3 · Chỗ khó & kịch bản | 11 | `spec.md` §5-§6 |
| R4 · Kiểm thử | 15 | `spec.md` §7 + `eval/` |
| R5 · Prototype | 8 | `codebase/` + demo |
| R6 · Validation | 8 | `validation/` |
| R7 · Quy trình & repo | 3 | cấu trúc repo + README phân công có tên |

## Ràng buộc cứng khi viết/sửa artifact

- `spec.md` theo đúng khung §1–§9 của `03-template-ai-spec.md`.
- **Quality bar chốt tại 23:59 ngày 1 và giữ nguyên sau đó.** Không hạ bar khi kết quả thấp — không đạt bar mà phân tích được nguyên nhân vẫn ăn đủ điểm; số liệu bị chỉnh sửa hoặc che giấu thì mất điểm.
- Mọi thay đổi từ feedback phải vào Changelog `spec.md` §9, trỏ về feedback/case cụ thể.
- Golden set ≥20 case: ≥2 case/lớp chỗ khó + 8–10 case thường + 2–4 case hiếm, trong đó ≥10 case từ chatlog thật. Quality bar hiện tại (gợi ý trong `docs/`): ≥80% detect đúng scope · ≥75% citation đúng · 0 case bịa nội dung · 100% low-confidence/out-of-scope có hỏi lại/từ chối hữu ích/chuyển TA.
- Chạy eval theo nhịp: chạy trọn bộ → bảng % → sửa MỘT failure đau nhất → **chạy lại trọn bộ**. Mỗi lượt một bản ghi trong `eval/`, ghi đủ mọi case kể cả fail.
- Prototype mức nào (Sketch/Mock/Working) cũng phải có **≥1 lời gọi AI chạy thật** ở quyết định trung tâm, có log/trace trong repo; phần mock ghi rõ trong spec §4.
- **4 lớp chỗ khó ①②③④** (① nguồn sự thật · ② mơ hồ/thiếu thông tin · ③ ngoài phạm vi/thẩm quyền · ④ đặc thù domain) là taxonomy dùng xuyên suốt spec §5, golden set và kịch bản demo.
- **Vibe-coding rule:** phần mang tên ai thì người đó phải giải thích được (kiểm tra ngẫu nhiên tại CP5/CP6). Khi build hộ, luôn kèm giải thích ngắn cách nó hoạt động — đừng chỉ đưa code.

## Điều hướng

- `docs/README.md` là mục lục tài liệu nhóm. Đọc `docs/agent-context-vlearn-smart-contextual-companion.md` trước khi làm bất cứ việc gì thuộc đề tài — đây là bản canonical của đề tài, sửa ở đó. (Từng có một bản nháp 264 dòng ở root, đã xoá tại commit `71d33d9`; cần chi tiết demo case / HAX-PAIR mapping / buzzwords bị lược thì `git show 87c2362` lấy lại.)
- `docs/vlearn-tutor-diem-yeu.md` — ghi chép test tay VLearn Tutor, nguồn evidence định tính bổ sung: không đọc được nội dung slide dạng ảnh · chưa có tính năng tóm tắt · self-confidence ~60% · quota ~15 câu/ngày · latency 5–10s · nhưng chặn prompt injection tốt và không bịa số liệu.

## Hai bản prototype song song

Repo hiện có hai surface, đừng nhầm khi sửa:

| Thư mục | Là gì | Dùng khi |
|---|---|---|
| `frontend/` | HTML + CSS + JS thuần, bám sát giao diện VLearn thật | Demo trực quan, không có backend |
| `codebase/` | Streamlit + Python, có scope detector và lời gọi Gemini thật, ghi trace ra `runs/` | Chứng minh quyết định AI + evidence cho R5 |

`codebase/README.md` có bảng khai rõ phần nào thật, phần nào mock — R5 chấm "mức prototype khai báo khớp thực tế". Lõi logic nằm trong `codebase/companion/`, tách rời Streamlit nên eval CP3 gọi lại được mà không cần UI.
- `tham-khao/` chỉ tra khi cần: JTBD Playbook chương 2 (job statement) + chương 3 (job map 8 bước). Không đọc hết 48 trang.
