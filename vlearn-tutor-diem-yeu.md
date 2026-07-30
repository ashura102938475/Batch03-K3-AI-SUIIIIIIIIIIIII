# Tổng hợp điểm yếu của VLearn Tutor

## Bối cảnh kiểm tra

Team thử tương tác trực tiếp với VLearn Tutor trong bài giảng COMP2010 để đánh giá khả năng hỗ trợ học viên khi xem lại nội dung buổi học. Các kịch bản test gồm hỏi khái niệm cơ bản, hỏi thông tin theo slide, hỏi thông tin ngoài tài liệu, thử prompt injection và hỏi về nội dung đang hiển thị trên slide.

## Phát hiện chính

### 1. Không đọc hiểu tốt nội dung trực quan trên slide

Điểm yếu rõ nhất là VLearn Tutor không thật sự hiểu nội dung slide đang hiển thị nếu nội dung đó nằm trong hình ảnh, layout đồ họa hoặc không được trích xuất thành text. Khi chuyển tới một slide có các gạch đầu dòng rõ ràng về mục tiêu buổi học và hỏi “Slide này đang hiển thị nội dung gì?”, Tutor trả lời rằng không tìm thấy nội dung cụ thể trong tài liệu.

Điều này cho thấy Tutor có thể đang phụ thuộc vào lớp text đã được index sẵn, thay vì đọc trực tiếp slide hiện tại theo ngữ cảnh người học đang xem.

### 2. Chưa có tính năng tóm tắt slide hoặc buổi học

Tutor có thể trả lời từng câu hỏi riêng lẻ, nhưng chưa hỗ trợ trực tiếp việc tóm tắt slide hiện tại, cụm slide hoặc toàn bộ buổi học. Với học viên muốn ôn lại nhanh, việc phải tự đặt nhiều câu hỏi nhỏ làm tăng thời gian và công sức.

Nhu cầu còn thiếu:

- Tóm tắt ý chính của slide hiện tại.
- Tóm tắt toàn bộ buổi học.
- Rút ra khái niệm quan trọng.
- Gợi ý phần cần ôn lại.
- Tạo câu hỏi kiểm tra nhanh sau bài học.

### 3. Độ tin cậy tự đánh giá chỉ ở mức trung bình

Một số câu trả lời cơ bản, ví dụ về “Prompt engineering là gì?”, được Tutor gắn mức tin cậy khoảng `60% · Trung bình`. Điều này cho thấy hệ thống truy xuất ngữ cảnh có thể chưa đủ chắc chắn, kể cả với các câu hỏi tương đối phổ biến trong nội dung học.

### 4. Quota hỏi đáp hạn chế

Tutor giới hạn khoảng 15 câu hỏi mỗi ngày. Sau vài câu test, quota đã giảm đáng kể. Với học viên cần hỏi nhiều để hiểu bài, ôn tập hoặc làm bài tập, giới hạn này dễ trở thành rào cản.

### 5. Tốc độ phản hồi còn chậm

Mỗi câu trả lời thường mất khoảng 5-10 giây, đôi khi lâu hơn. Khi học viên đang xem lại bài hoặc cần hỏi liên tục, độ trễ này làm giảm trải nghiệm học tập.

## Điểm tích cực ghi nhận

VLearn Tutor xử lý khá tốt các tình huống an toàn:

- Từ chối prompt injection như yêu cầu bỏ qua hướng dẫn hệ thống.
- Không bịa số liệu khi bị hỏi thông tin không có trong slide.
- Biết nói không có dữ liệu và gợi ý nguồn khác khi cần.

Điều này cho thấy hệ thống có nền tảng an toàn tương đối tốt, nhưng còn thiếu năng lực hỗ trợ ôn tập theo ngữ cảnh slide.

## Tác động đến học viên

Các điểm yếu trên khiến học viên gặp khó khi muốn ôn lại bài nhanh sau buổi học. Nếu slide dài, có nhiều hình ảnh hoặc nội dung nằm trong layout phức tạp, người học vẫn phải tự đọc và tự tổng hợp. Tutor chưa giảm đáng kể công sức trong các tác vụ như nắm ý chính, tìm phần trọng tâm, hoặc biến nội dung bài học thành checklist ôn tập.

## Cơ hội sản phẩm

Team có thể tập trung vào hướng: **AI tóm tắt slide và buổi học cho VLearn**.

Giải pháp nên ưu tiên:

- Đọc được nội dung slide hiện tại, kể cả nội dung trực quan.
- Tóm tắt ngắn gọn theo từng slide hoặc toàn bộ buổi học.
- Trích dẫn nguồn theo số slide hoặc đoạn transcript.
- Tạo danh sách khái niệm quan trọng và câu hỏi tự kiểm tra.
- Giảm số lượt hỏi cần thiết, phù hợp với giới hạn quota hiện tại.

## Giả thuyết cần khảo sát thêm

1. Học viên có thường xuyên cần xem lại slide sau buổi học không?
2. Học viên mất bao lâu để tự tóm tắt một buổi học?
3. Học viên cần tóm tắt theo slide, theo chủ đề, hay theo checklist ôn tập?
4. Tính năng tóm tắt có giúp giảm số câu hỏi phải gửi cho Tutor không?
5. Học viên có tin tưởng hơn nếu bản tóm tắt có trích dẫn slide hoặc transcript không?
