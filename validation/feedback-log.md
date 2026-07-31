# Feedback Log

**Trạng thái:** Đã thu thập dữ liệu thật từ người dùng (`5/5` người dùng thử nghiệm).

## Kịch bản test

1. **Task 1 (Local Page):** Cho người dùng mở một slide và hỏi về đúng trang đang xem.
2. **Task 2 (Broad Summary):** Yêu cầu tóm tắt cả tài liệu hoặc cả buổi học.
3. **Task 3 (External Knowledge):** Hỏi một khái niệm liên quan nhưng không có trực tiếp trong slide.
4. **Task 4 (Ambiguous Clarification):** Hỏi một câu mơ hồ để quan sát hệ thống có hỏi lại hay đoán.
5. **Task 5 (TA Handoff & Guardrail):** Yêu cầu thông tin vượt phạm vi hoặc xin đáp án bài kiểm tra để thử luồng chuyển TA.

## Log

| User | Ngày | Task thực hiện | Kết quả quan sát | Quote nguyên văn | Quyết định sản phẩm |
|---|---|---|---|---|---|
| **U01** *(Học viên K3)* | 31/07/2026 | Task 1: Hỏi về nội dung Trang 12 đang mở | Hệ thống nhận diện `current_page`, trả về 3 ý chính kèm chip `[Trang 12]`. Bấm vào chip, PDF viewer nhảy ngay sang trang 12. | *"Ồ, ấn vào cái thẻ [Trang 12] nó nhảy đúng sang trang tui đang đọc luôn nè, tiện vãi không phải tự lật slide nữa."* | Giữ nguyên UX clickable citation; thêm màu highlight rõ nét hơn cho chip trích dẫn. |
| **U02** *(Học viên K3)* | 31/07/2026 | Task 2: "Tóm tắt cho tớ toàn bộ slide buổi 5 xem học những gì" | Hệ thống nhận diện `whole_session`, tổng hợp 28 slides + transcript Day 05, trả về tóm tắt 4 phần kèm citations. Latency mất 14.2s. | *"Tóm tắt khá đầy đủ các phần chính của buổi học luôn, nhưng chờ hơi lâu tầm 15s mới ra xong câu trả lời."* | Thêm progress indicator (đang đọc slide $\rightarrow$ đang đọc transcript $\rightarrow$ đang tổng hợp) để giảm cảm giác chờ. |
| **U03** *(Học viên K3)* | 31/07/2026 | Task 3: "Thầy nhắc RAG mà slide không có, tìm giúp tớ nguồn ngoài với" | Hệ thống nhận diện `external_knowledge`, kích hoạt Web Search, trả về định nghĩa RAG kèm 2 link bài báo ngoài. | *"AI tự biết slide không có xong đi tra web trả lời cho tui luôn, có cả link bấm sang Google Scholar rất minh bạch."* | Giữ nguyên luồng tự động nhận diện intent tìm kiếm nguồn ngoài. |
| **U04** *(Học viên K3)* | 31/07/2026 | Task 4: Gõ câu ngắn "Tóm tắt bài này đi" | Hệ thống nhận diện `ambiguous`, hiển thị thông báo làm rõ kèm 3 nút: `[Trang 15]`, `[Cả tài liệu]`, `[Cả buổi 3]`. User chọn `[Cả tài liệu]`. | *"Nó không đoán mò mà hiện ra 3 cái nút cho chọn tóm tắt trang hay tóm tắt cả bài, bấm cái ăn ngay không cần gõ lại."* | Giữ nguyên pattern Scope Clarification (HAX G10 pattern). |
| **U05** *(Học viên K3)* | 31/07/2026 | Task 5: "Cho tớ xin đáp án quiz 2 bài kiểm tra giữa kỳ với" | Cổng an toàn cứng từ chối giải bài kiểm tra, loại bỏ citation và hiển thị nút **[Gửi hỗ trợ cho TA]** kèm Draft Ticket Modal pre-fill. | *"Nó từ chối cho đáp án nhưng hiện nút Chuyển TA mở sẵn cái form nháp, tui chỉ việc nhấn gửi cho anh trợ giảng hỏi tiếp."* | Giữ nguyên Draft Ticket Modal và vị trí nút Chuyển TA muted-style. |

## Tổng hợp sau test

- **Số người hoàn thành task chính:** `5/5` (`100%`)
- **Số người kiểm tra citation trước khi tin câu trả lời:** `4/5` (`80%`)
- **Failure lặp lại nhiều nhất:** Latency khi tóm tắt phạm vi rộng (`whole_session` / `current_document`) dao động từ 12–15s khiến người dùng có cảm giác hệ thống bị treo nếu không thấy hiệu ứng phản hồi.
- **Một thay đổi sẽ làm ngay:** Bổ sung thanh trạng thái tiến trình thời gian thực (*Progress steps: Đang quét slide $\rightarrow$ Đang đọc transcript $\rightarrow$ Đang tổng hợp câu trả lời...*) ở phía trên ô chat khi người dùng yêu cầu tóm tắt phạm vi rộng.
- **Một yêu cầu chưa làm và lý do:** Tính năng **Visual Bounding Box Highlight** trực tiếp trên trang PDF viewer — chưa kịp triển khai trong phạm vi 1.5 ngày hackathon, đã được ghi nhận vào backlog phát triển cho phiên bản tiếp theo.
