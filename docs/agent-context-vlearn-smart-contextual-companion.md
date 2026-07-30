# Agent Context - VLearn Smart Contextual Companion

File này dùng để đưa cho AI agent hoặc thành viên mới trong nhóm đọc nhanh trước khi viết spec, build prototype, làm eval, hoặc chuẩn bị slide.

## 1. Tên đề tài

**VLearn Smart Contextual Companion**

## 2. Ý tưởng chính

Cải thiện chất lượng phản hồi của VLearn Tutor bằng cách nhận diện đúng phạm vi ngữ cảnh học liệu, truy xuất và trích dẫn đúng slide liên quan, bổ sung kiến thức nền khi cần, và chuyển tiếp TA trong các trường hợp vượt phạm vi hoặc độ tin cậy thấp.

Nói ngắn gọn:

> Biến VLearn Tutor từ chatbot trả lời theo trang hiện tại thành một learning companion hiểu đúng phạm vi học liệu, trả lời có căn cứ, cite đúng nguồn, và biết khi nào cần hỏi lại hoặc chuyển TA.

## 3. Bối cảnh sản phẩm

VLearn là nền tảng học liệu của khóa AI Thực Chiến. Học viên đọc slide/tài liệu trên giao diện VLearn và có VLearn Tutor ở cạnh phải để hỏi bài.

Vấn đề quan sát được: khi học viên hỏi các câu như "tóm tắt buổi 5", "tóm tắt bài buổi 6", "tóm tắt toàn bộ slide này", tutor hiện tại thường chỉ nhìn trang đang mở hoặc đoạn bôi đen, rồi trả lời thiếu context, nói không truy xuất được toàn bộ tài liệu, hoặc citation rỗng/sai phạm vi.

## 4. Job Executor

**Học viên K3 đang học hoặc ôn lại tài liệu trên VLearn.**

Không viết là "học viên nói chung". User cụ thể là người đang ở trong flow học tập: mở slide, xem một trang, rồi hỏi tutor để hiểu nhanh nội dung.

## 5. Job Statement

> Nắm nhanh nội dung chính của một slide, một tài liệu hoặc một buổi học để biết phần nào cần học, cần note, hoặc cần hỏi thêm.

Job này vẫn tồn tại dù không có AI: học viên vẫn phải tự đọc slide, tua video, hỏi bạn, hỏi TA, hoặc copy nội dung sang ChatGPT.

## 6. Pain Statement

> Học viên đang hỏi/tóm tắt nội dung học liệu trên VLearn nhưng tutor thường chỉ hiểu đoạn bôi đen hoặc trang hiện tại, không nhận ra phạm vi rộng hơn như tài liệu hoặc buổi học, khiến câu trả lời thiếu context, citation yếu, hoặc từ chối không hữu ích; học viên phải tự mở lại tài liệu, hỏi lại nhiều lần hoặc chuyển sang công cụ khác.

## 7. Evidence Từ Data

Nguồn data:

- `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`
- 1,261 lượt hỏi-đáp student-tutor
- 369 users
- 585 conversations
- Dữ liệu đã ẩn danh

Các số liệu chính đã mining:

- `156/1,261` lượt hỏi (`12.4%`) có nhu cầu summary/tổng hợp/ý chính/keyword/note.
- `62` lượt hỏi summary ở phạm vi rộng như toàn bài, toàn buổi, file tài liệu, slide day.
- `87/156` lượt summary (`55.8%`) gặp phản hồi kiểu "không tìm thấy / không truy cập được / rất tiếc".
- `101/156` lượt summary (`64.7%`) không có citation.
- Tổng thể `582/1,261` lượt tutor trả lời citation rỗng (`46.2%`).
- Với summary có thông tin trang trong prompt, chỉ `16/155` lượt cite đúng trang context; `100/155` lượt không cite gì.

Rating chỉ dùng như tín hiệu phụ vì ít lượt được rating:

- Summary có rating: `10/14` là downvote (`71.4%`).
- Các câu trả lời kiểu no-access có rating: `20/20` là downvote.
- Câu trả lời citation rỗng có rating: `29/41` là downvote (`70.7%`).

Ví dụ evidence nên trích trong spec/slide:

- `T0408`: user hỏi "tóm tắt các chủ đề chính của slide day05..." nhưng tutor nói không thể tìm thấy file/nội dung chi tiết.
- `T1164`: user hỏi "tóm tắt cho t tất cả từ trang 1 đến trang 44 bài này học về gì" nhưng tutor nói không thể truy xuất tóm tắt tổng thể toàn bộ tài liệu.
- `T0213`: user hỏi "tóm tắt tất cả slide" nhưng tutor nói hệ thống không thể tự động tổng hợp toàn bộ slide trong một lần.
- `T0649`: user hỏi "tóm tắt nội dung chính trong slide này" nhưng tutor nói không tìm thấy nội dung cụ thể cho slide 37.

## 8. Lát Cắt Một Câu

> Học viên đang ôn lại trên VLearn hỏi về một slide/tài liệu/buổi học, hệ thống nhận diện đúng phạm vi context cần đọc, truy xuất slide liên quan và trả lời có citation hoặc chuyển TA khi độ tin cậy thấp.

## 9. Non-goals

- Không build lại toàn bộ VLearn.
- Không sửa mọi loại câu hỏi của tutor.
- Không làm chatbot Discord.
- Không làm full LMS hoặc hệ thống quản lý khóa học.
- Không cam kết trả lời đúng mọi câu hỏi ngoài tài liệu.
- Không dùng dữ liệu thật ngoài data pack hoặc dữ liệu đã được phép dùng.

## 10. Giải Pháp Sơ Bộ

Core idea: trước khi trả lời, hệ thống phải hiểu user đang hỏi ở phạm vi nào.

1. Detect intent: summary / explain / logistics / out-of-scope / prompt attack.
2. Detect scope: selected text / current page / current document / whole session.
3. Retrieve context theo scope đã chọn.
4. Generate grounded response có citation.
5. Low confidence hoặc out-of-scope -> hỏi lại, từ chối hữu ích, hoặc chuyển TA.

## 11. Output Format Gợi Ý

```text
Phạm vi đã hiểu: [Trang hiện tại / Tài liệu hiện tại / Buổi học]
Độ tin cậy: [cao / trung bình / thấp]

Tổng quan:
- ...

Ý chính:
1. ...
2. ...
3. ...

Keyword cần nhớ:
- ...

Phần dễ nhầm:
- ...

Nguồn:
- [Trang X]
- [Transcript Txx-NNN] nếu dùng transcript

Hành động tiếp theo:
- [Hỏi tiếp] [Tạo câu hỏi ôn tập] [Chuyển TA]
```

## 12. Automation

**Conditional automation**

- AI tự trả lời khi tìm được căn cứ và citation đủ tin cậy.
- Nếu thiếu dữ liệu, scope mơ hồ, hoặc câu hỏi vượt phạm vi thì hỏi lại/chuyển TA.
- Trả lời sai có thể làm học viên hiểu sai kiến thức, nên không nên automate tuyệt đối.

## 13. 4 Lớp Chỗ Khó

1. **Nguồn sự thật**: AI có thể bịa nội dung nếu không lấy được đúng slide/transcript.
2. **Mơ hồ / thiếu thông tin**: user nói "tóm tắt bài này" nhưng không rõ là trang, file hay buổi.
3. **Ngoài phạm vi / thẩm quyền**: user hỏi tải file, deadline, API key, password, hoặc thông tin không nằm trong học liệu.
4. **Đặc thù domain**: sai nội dung kiến thức làm học viên học sai, mất niềm tin, hoặc trả lời sai bài/lab.

## 14. Golden Set Gợi Ý

- 8 case hỏi slide/trang hiện tại.
- 6 case hỏi toàn tài liệu.
- 4 case hỏi toàn buổi.
- 2 case thiếu dữ liệu / ngoài phạm vi / prompt attack.

Nên có ít nhất 10 case lấy từ chatlog thật, ghi bằng `turn_id` thay vì copy dài toàn bộ dữ liệu.

## 15. Quality Bar Gợi Ý

- >=80% case nhận diện đúng scope.
- >=75% câu trả lời có citation đúng.
- 0 case bịa nội dung ngoài tài liệu.
- 100% low-confidence/out-of-scope case có hỏi lại, từ chối hữu ích, hoặc chuyển TA.

## 16. Lưu Ý Cho AI Agent

- Luôn bám đề tài: context understanding + citation + confidence + TA handoff.
- Không mở rộng sang chatbot tổng quát.
- Khi viết spec, luôn đưa số liệu evidence kèm phương pháp đếm.
- Khi tạo prototype, ưu tiên flow chạy được hơn UI đẹp.
- Khi tạo eval, phải có case cho 4 scope: selected text, current page, current document, whole session.
- Khi dùng data pack, không copy nguyên văn dài; trích ngắn và ghi `turn_id`/mã transcript.
- Khi không chắc, ghi là "cần validation thêm" thay vì khẳng định quá mức.

