# Data Analysis - VLearn Smart Contextual Companion

## 1. Mục Tiêu Phân Tích

Mục tiêu là kiểm chứng giả thiết cho đề tài **VLearn Smart Contextual Companion**:

> VLearn Tutor hiện tại chưa hiểu tốt phạm vi ngữ cảnh học liệu mà học viên đang hỏi, đặc biệt với các câu summary/tổng hợp theo slide, tài liệu hoặc toàn buổi học. Điều này dẫn tới câu trả lời thiếu context, citation rỗng/sai phạm vi, hoặc phản hồi "không tìm thấy / không truy cập được" dù user đang ở trong học liệu.

## 2. Câu Hỏi Cần Kiểm Chứng

Theo CP1, nhóm cần trả lời 5 câu hỏi khám phá. Data thực hỗ trợ mạnh nhất cho các câu sau:

| Câu hỏi | Data kiểm chứng được không? | Cách kiểm chứng |
|---|---:|---|
| Ai là người trực tiếp làm việc này? | Một phần | Data cho biết user là học viên dùng VLearn `in_class`, nhưng chưa biết chính xác đang học trong buổi, ôn quiz hay học bù. Cần khảo sát thêm. |
| Họ đang cố hoàn thành việc gì? | Có | Đếm intent summary/tổng hợp/ý chính/keyword/note trong câu hỏi học viên. |
| Hôm nay họ giải quyết bằng gì, fail ở đâu? | Một phần | Data cho thấy tutor hiện tại fail ở citation/context/no-access. Cần khảo sát thêm để biết họ chuyển sang ChatGPT, hỏi bạn, hỏi TA hay tự đọc. |
| Bằng chứng nào cho thấy họ đau thật? | Có | Có số đếm, turn ID, ví dụ nguyên văn ngắn, rating phụ. |
| Vì sao chọn hướng này thay vì hướng khác? | Một phần | Có thể so sánh tần suất pain trong chatlog; cần khảo sát để đo "mỗi lần tốn gì". |

## 3. Nguồn Data

File:

`codebase/data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`

Quy mô:

- `2,522` dòng message
- `1,261` lượt hỏi-đáp student-tutor
- `369` users
- `585` conversations
- Giai đoạn: `22/07 -> 29/07/2026`
- Dữ liệu đã ẩn danh

Field dùng để phân tích:

- `role`: phân biệt student/tutor
- `turn_id`: ghép một lượt hỏi-đáp
- `user_id`, `conversation_id`: đếm số user/conversation bị ảnh hưởng
- `content`: nội dung câu hỏi/câu trả lời
- `citations`: nguồn tutor trích dẫn
- `rating`: up/down của học viên
- `day_code`: tài liệu/ngày học
- `avg_latency_ms`, `total_input_tokens`, `total_output_tokens`: dùng phụ, không phải trọng tâm

## 4. Phương Pháp Mining

### 4.1 Ghép lượt hỏi-đáp

Lọc:

- student rows: `role == "student"`
- tutor rows: `role == "tutor"`
- merge theo `turn_id`

Kết quả: `1,261` lượt hỏi-đáp.

### 4.2 Tách query thật

Trong `content` của student thường có metadata dạng:

```text
(Trang N, đoạn được chọn: "...")
câu hỏi thật của user
```

Khi đếm intent, chỉ đếm phần câu hỏi thật sau metadata, không đếm phần đoạn bôi đen. Việc này giúp tránh phóng đại số liệu.

### 4.3 Chuẩn hóa tiếng Việt

Đưa text về dạng lowercase và bỏ dấu để đếm keyword ổn định:

- `tóm tắt` -> `tom tat`
- `tổng hợp` -> `tong hop`
- `không tìm thấy` -> `khong tim thay`

### 4.4 Rule đếm chính

**Summary intent**

Đếm câu hỏi chứa các nhóm từ:

- `tom tat`
- `tom gon`
- `summary`
- `tong hop`
- `noi dung chinh`
- `y chinh`
- `keyword`
- `note`
- `can hoc`
- `noi dung quan trong`

**Broad scope**

Đếm câu hỏi chứa các tín hiệu phạm vi rộng:

- `toan bo`
- `tat ca`
- `ca bai`
- `bai nay`
- `buoi`
- `day 1` -> `day 6`
- `file nay`
- `tai lieu nay`
- `slide pdf`
- `slide day`

**No-access reply**

Đếm câu trả lời tutor chứa các tín hiệu:

- `khong tim thay`
- `khong the truy cap`
- `khong the truy xuat`
- `khong co thong tin`
- `hien khong`
- `rat tiec`
- `khong hien thi`
- `chua tim thay`

**Citation rỗng**

Đếm `citations == []` hoặc missing.

**Citation khớp trang context**

Nếu prompt student có `Trang N`, parse `N`. Citation được coi là khớp context page nếu `N` nằm trong danh sách `citations`.

Lưu ý: với câu broad-scope, cite đúng trang hiện tại không phải đủ để chứng minh trả lời đúng toàn buổi. Số này chỉ dùng để cho thấy citation hiện tại còn yếu và hay rỗng.

## 5. Kết Quả Chính

### 5.1 Nhu cầu summary/tổng hợp có thật

- `156/1,261` lượt hỏi (`12.4%`) có nhu cầu summary/tổng hợp/ý chính/keyword/note.
- Các lượt này đến từ `111` users.
- `62` lượt hỏi summary ở phạm vi rộng như toàn bài, toàn buổi, file tài liệu, slide day.

Ý nghĩa:

> Summary/tổng hợp không phải edge case. Đây là một nhu cầu lặp lại trong hành vi học tập trên VLearn.

### 5.2 Tutor hiện tại fail nhiều ở nhóm summary

- `87/156` lượt summary (`55.8%`) gặp phản hồi kiểu "không tìm thấy / không truy cập được / rất tiếc".
- `101/156` lượt summary (`64.7%`) không có citation.
- Với summary broad-scope: `40/62` lượt có no-access reply, `42/62` lượt citation rỗng.

Ý nghĩa:

> Pain chính không chỉ là câu chữ chưa hay. Tutor chưa chọn đúng phạm vi context để retrieval/trả lời.

### 5.3 Citation là điểm yếu rõ

Tổng thể:

- `582/1,261` lượt tutor trả lời citation rỗng (`46.2%`).

Riêng summary:

- `101/156` lượt summary không có citation (`64.7%`).

Với summary có thông tin trang trong prompt:

- `16/155` lượt cite đúng trang context (`10.3%`).
- `100/155` lượt không cite gì (`64.5%`).
- `39/155` lượt có citation nhưng không cite trang context (`25.2%`).

Ý nghĩa:

> Đề tài nên nhấn mạnh "citation-first response" và "scope-aware retrieval", không chỉ "summary tốt hơn".

### 5.4 Rating phụ ủng hộ pain

Rating rất ít, nên không dùng làm bằng chứng chính. Tuy vậy, tín hiệu khá rõ:

- Summary có rating: `10/14` là downvote (`71.4%`).
- No-access reply có rating: `20/20` là downvote.
- Citation rỗng có rating: `29/41` là downvote (`70.7%`).

Ý nghĩa:

> Khi user có rating, các câu trả lời thiếu căn cứ/no-access có xu hướng bị đánh giá xấu.

### 5.5 Handoff có đất làm nhưng là phụ

Một số nhóm câu nên chuyển TA hoặc từ chối hữu ích:

- `22` lượt liên quan logistics/download/nộp bài/file PDF/repo.
- `10` lượt có dấu hiệu prompt injection/API key/password/base64.

Ý nghĩa:

> TA handoff nên là feature phụ cho low-confidence/out-of-scope, không phải core value chính.

## 6. Evidence Turn IDs

Không nên copy dài nguyên văn data vào repo nộp bài. Khi cần minh họa, dùng turn ID và trích ngắn.

### Broad summary failed

- `T0408`: user hỏi tóm tắt chủ đề chính của slide Day 5, tutor nói không tìm thấy file/nội dung chi tiết.
- `T1164`: user hỏi tóm tắt từ trang 1 đến trang 44, tutor nói không thể truy xuất tóm tắt tổng thể toàn bộ tài liệu.
- `T0213`: user hỏi tóm tắt tất cả slide, tutor nói không thể tự động tổng hợp toàn bộ slide trong một lần.
- `T0345`: user hỏi tóm tắt slide Day 4, tutor nói chưa có nội dung tóm tắt cụ thể cho toàn bộ ngày học.

### Local summary failed

- `T0649`: user hỏi tóm tắt nội dung chính trong slide này, tutor nói không tìm thấy nội dung cụ thể cho slide 37.
- `T0523`: user hỏi tóm tắt slide này, tutor nói không tìm thấy nội dung cụ thể cho trang 9.

### Citation mismatch / citation weak

- `T0520`: metadata context page là 96, user hỏi về Trang 63, tutor cite `[63]`. Đây là case cho thấy cần parse đúng câu hỏi và scope, không chỉ metadata trang hiện tại.
- `T1108`: user hỏi đoạn ở Trang 12, tutor cite `[17, 42]`.
- `T0399`: user hỏi biểu đồ được bôi đỏ trên trang 6, tutor trả no-access nhưng có citation `[71]`.

### Handoff / out-of-scope candidates

- `T0707`: hỏi về download tài liệu.
- `T1027`: hỏi hướng dẫn bài lab và cách nộp.
- `T0794`: hỏi admin password/API key.
- `T0582`: yêu cầu mã hóa base64 toàn bộ nội dung.

## 7. Kết Luận Cho Đề Tài

Data ủng hộ 3 luận điểm:

1. Học viên có nhu cầu thật trong việc tóm tắt/tổng hợp học liệu.
2. Tutor hiện tại fail đáng kể ở nhóm câu hỏi cần hiểu scope/context rộng.
3. Citation/grounding là điểm yếu rõ, đặc biệt trong nhóm summary.

Vì vậy, đề tài nên định vị là:

> Cải thiện VLearn Tutor bằng scope-aware retrieval, citation-first response và conditional TA handoff.

Không nên định vị là:

> Làm chatbot thông minh hơn nói chung.

## 8. Cách Dùng Số Liệu Trong Canvas

Dòng evidence gọn:

> Mining `1,261` lượt hỏi-đáp VLearn: `156/1,261` lượt (`12.4%`) có nhu cầu summary/tổng hợp; `87/156` lượt summary (`55.8%`) gặp phản hồi kiểu "không tìm thấy / không truy cập được / rất tiếc"; `101/156` lượt summary (`64.7%`) không có citation; tổng thể `582/1,261` lượt tutor trả lời citation rỗng (`46.2%`).

## 9. Cách Dùng Số Liệu Trong Slide

Slide problem:

- `46.2%` câu trả lời có citation rỗng.
- `87/156` lượt summary gặp phản hồi kiểu không tìm thấy/không truy cập được.
- `101/156` lượt summary không có citation.

Slide user job:

- `156/1,261` lượt có nhu cầu summary/tổng hợp.
- `62` lượt hỏi summary ở phạm vi rộng như toàn bài/toàn buổi/file tài liệu/slide day.
- Với summary có thông tin trang trong prompt, chỉ `16/155` lượt cite đúng trang context; `100/155` lượt không cite gì.

## 10. Giới Hạn Phân Tích

- Đây là keyword mining, chưa phải manual labeling toàn bộ.
- Rating ít, chỉ nên dùng như tín hiệu phụ.
- Data VLearn không cho biết user sau khi tutor fail thì làm gì tiếp. Cần khảo sát thêm.
- Data không đo trực tiếp "mất bao nhiêu phút"; cần phỏng vấn hoặc validation.
- Citation đúng trang chưa đồng nghĩa câu trả lời đúng hoàn toàn; cần eval thủ công/golden set.

## 11. Câu Hỏi Khảo Sát Nên Bổ Sung

Hỏi ít nhất 20 học viên ngoài nhóm:

1. Lần gần nhất bạn muốn tóm tắt một slide/tài liệu/buổi học trên VLearn, bạn làm bằng cách nào?
2. Lần đó mất khoảng bao lâu?
3. Khi VLearn Tutor chỉ trả lời theo trang hiện tại hoặc nói không truy cập được toàn bộ tài liệu, bạn làm gì tiếp?
4. Bạn có tin câu trả lời hơn nếu nó hiện rõ phạm vi đã đọc và citation tới slide không? Vì sao?

## 12. Gợi Ý Golden Set Từ Analysis

20 case:

- 8 case local scope: tóm tắt/giải thích trang hiện tại hoặc đoạn bôi đen.
- 6 case document scope: tóm tắt file/tài liệu hiện tại.
- 4 case session scope: tóm tắt toàn buổi hoặc Day N.
- 2 case out-of-scope/security/logistics: download, deadline, password/API key.

Quality bar:

- >=80% detect đúng scope.
- >=75% câu trả lời có citation đúng.
- 0 case bịa nội dung ngoài tài liệu.
- 100% low-confidence/out-of-scope case hỏi lại, từ chối hữu ích, hoặc chuyển TA.

## 13. Script Mining Tham Khảo

Pseudo-code:

```python
import pandas as pd

df = pd.read_csv("codebase/data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv")
student = df[df.role == "student"]
tutor = df[df.role == "tutor"]
pairs = student.merge(tutor, on="turn_id", suffixes=("_student", "_tutor"))

# 1. Extract user query after metadata.
# 2. Normalize Vietnamese text: lowercase, remove accents.
# 3. Count summary keywords on query only.
# 4. Count no-access keywords on tutor answer.
# 5. Parse citations and count empty list.
# 6. Parse "Trang N" from prompt and compare with citation list.
```

Khi nộp spec, mô tả phương pháp đếm bằng lời là đủ; không cần nộp toàn bộ script nếu không build eval tự động.
