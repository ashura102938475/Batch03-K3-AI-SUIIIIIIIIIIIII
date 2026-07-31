# CP1 Canvas & Slide Script - VLearn Smart Contextual Companion

## Ý tưởng chính

> Cải thiện chất lượng phản hồi của VLearn Tutor bằng cách nhận diện đúng phạm vi ngữ cảnh học liệu, truy xuất và trích dẫn đúng slide liên quan, bổ sung kiến thức nền khi cần, và chuyển tiếp TA trong các trường hợp vượt phạm vi hoặc độ tin cậy thấp.

## CP1 Canvas 7 Dòng

| # | Mục | Nội dung điền |
|---|---|---|
| 1 | **Chiến tuyến: VLearn / Discord / Hướng mở** | **VLearn AI Tutor** - tối ưu tutor hiện có trên VLearn |
| 2 | **Ai đang làm việc này - một vai cụ thể** | **Học viên K3 đang học/ôn lại tài liệu trên VLearn**, đặc biệt khi muốn hiểu nhanh nội dung của một slide, một tài liệu hoặc cả buổi học |
| 3 | **Họ vướng gì - ai, đang làm gì, vướng đâu, hậu quả gì** | Học viên đang hỏi/tóm tắt nội dung học liệu trên VLearn nhưng tutor thường chỉ hiểu đoạn bôi đen/trang hiện tại, không nhận ra phạm vi rộng hơn như tài liệu hoặc buổi học, khiến câu trả lời thiếu context, citation yếu, hoặc từ chối không hữu ích; học viên phải tự mở lại tài liệu, hỏi lại nhiều lần hoặc chuyển sang công cụ khác |
| 4 | **1-2 bằng chứng đầu tiên** | Mining `1,261` lượt hỏi-đáp VLearn: `156/1,261` lượt (`12.4%`) có nhu cầu summary/tổng hợp; `87/156` lượt summary (`55.8%`) gặp phản hồi kiểu "không tìm thấy / không truy cập được / rất tiếc"; `101/156` lượt summary (`64.7%`) không có citation; tổng thể `582/1,261` lượt tutor trả lời citation rỗng (`46.2%`) |
| 5 | **Lát cắt MỘT CÂU** | Học viên đang ôn lại trên VLearn hỏi về một slide/tài liệu/buổi học, hệ thống nhận diện đúng phạm vi context cần đọc, truy xuất slide liên quan và trả lời có citation hoặc chuyển TA khi độ tin cậy thấp |
| 6 | **AI tự làm đến đâu + 1 dòng lý do** | **Conditional automation**: AI tự trả lời khi tìm được căn cứ và citation đủ tin cậy; nếu thiếu dữ liệu, scope mơ hồ, hoặc câu hỏi vượt phạm vi thì hỏi lại/chuyển TA, vì trả lời sai có thể làm học viên hiểu sai kiến thức |
| 7 | **>=3 người sẽ thử + phân công có tên** | **Blocker:** willing users chưa được xác nhận, không điền tên giả. Phân công: Nguyễn Chí Hiếu (`2A202601931`) evidence/eval/grounding/integration; Nguyễn Anh Trà (`2A202601735`) backend/API/retrieval/TA; Trần Văn Tài (`2A202601339`) frontend/PDF/citation UX; Bùi Gia Uy (`2A202601867`) prototype/routing/eval/docs. Owner validation/demo chưa chốt. |

## Slide 1 - Problem: Tutor đang nhìn hẹp

Key message: VLearn Tutor hiện tại thường dừng ở trang đang mở hoặc đoạn bôi đen.

Điểm nói:

- User hỏi: "Tóm tắt buổi 5/buổi 6 cho tôi"
- Tutor lại trả theo `Trang 1` hoặc nói không truy xuất được toàn bộ tài liệu
- Vấn đề không phải chỉ là "trả lời chưa hay", mà là **không hiểu đúng phạm vi context**

Số liệu:

- `46.2%` câu trả lời có citation rỗng
- `87/156` lượt summary gặp phản hồi kiểu không tìm thấy/không truy cập được
- `101/156` lượt summary không có citation

## Slide 2 - User Job & Pain

Key message: Học viên cần hiểu nhanh nội dung học liệu để học tiếp/ôn lại.

Job statement:

> Nắm nhanh nội dung chính của slide, tài liệu hoặc buổi học để biết phần nào cần học, cần note, hoặc cần hỏi thêm.

Pain:

- Muốn hỏi theo nhiều phạm vi: slide hiện tại, file PDF, toàn buổi học
- Tutor hiện tại chưa phân biệt tốt các phạm vi này
- Hệ quả: mất thời gian hỏi lại, chuyển sang ChatGPT/hỏi bạn/đọc thủ công

Số liệu:

- `156/1,261` lượt có nhu cầu summary/tổng hợp
- `62` lượt hỏi summary ở phạm vi rộng như toàn bài/toàn buổi/file tài liệu/slide day
- Với summary có thông tin trang trong prompt, chỉ `16/155` lượt cite đúng trang context; `100/155` lượt không cite gì

## Slide 3 - Solution: VLearn Smart Contextual Companion

Key message: Trước khi trả lời, hệ thống hiểu user đang hỏi trong phạm vi nào.

Core flow:

1. Detect intent: summary / explain / logistics / out-of-scope
2. Detect scope: selected text / current page / current document / whole session
3. Retrieve context: slide pages + transcript + metadata
4. Generate grounded response with citation
5. Low confidence -> ask clarification or handoff TA

Buzzwords dùng vừa đủ:

- Context-aware retrieval
- Scope-aware answering
- Citation-first response
- Human-in-the-loop TA handoff
- Grounded learning copilot

## Slide 4 - Prototype Flow

Key message: Demo một lát cắt nhỏ nhưng chạy được.

Demo case:

> Tóm tắt bài buổi 6 cho tôi đi

Prototype response:

- Scope detected: `Whole session - Day 6`
- Sources: `day06 PDF + transcript đoạn liên quan`
- Output:
  - Tổng quan
  - 3-5 ý chính
  - Keyword cần nhớ
  - Phần dễ nhầm
  - Citation tới slide/trang
  - "Hỏi TA" nếu thiếu dữ liệu hoặc confidence thấp

## Slide 5 - Evaluation

Key message: Không chỉ demo đẹp, có đo được chất lượng.

Golden set:

- 20 case
- 8 case hỏi slide/trang hiện tại
- 6 case hỏi toàn tài liệu
- 4 case hỏi toàn buổi
- 2 case thiếu dữ liệu / ngoài phạm vi

Quality bar gợi ý:

- >=80% nhận diện đúng scope
- >=75% câu trả lời có citation đúng
- 0 case bịa nội dung ngoài tài liệu
- 100% low-confidence case có hỏi lại hoặc chuyển TA

## Slide 6 - Impact & Next Step

Key message: Tutor đáng tin hơn vì hiểu đúng context và biết giới hạn.

Impact:

- Giảm câu trả lời "không tìm thấy" không hữu ích
- Tăng độ tin cậy nhờ citation đúng slide
- Giúp học viên ôn nhanh hơn
- Giảm tải TA bằng cách chỉ handoff case thật sự cần người hỗ trợ

Next step:

- Validate với >=5 học viên
- So sánh response hiện tại vs prototype
- Ghi feedback vào changelog trước demo

