# Reflection - Nguyễn Chí Hiếu

- Mã học viên: `2A202601931`
- GitHub: `Hieunc2910`
- Phụ trách chính: phân tích dữ liệu, golden set/evaluator, grounding/citation và
  tích hợp các nhánh.

## Phần tôi trực tiếp làm

- Phân tích 1.261 lượt hỏi đáp trong dữ liệu mẫu VLearn. Tôi tìm thấy 156 lượt có
  nhu cầu tóm tắt; 87 lượt nhận phản hồi kiểu không truy cập được và 101 lượt
  không có citation.
- Xây golden set v2, sau đó mở rộng thành v3 gồm 31 câu. Trong đó có 10 câu lấy từ
  quan sát thực tế, cùng các case sai chính tả, câu mơ hồ, nguồn ngoài, deadline và
  yêu cầu xin đáp án.
- Chỉnh evaluator để kiểm tra cả quyết định scope, nội dung trả lời, citation và lỗi
  critical, thay vì chỉ so nhãn nội bộ.
- Sửa một số lỗi grounding: không hiển thị citation khi không có câu trả lời thật,
  tách nguồn web khỏi nguồn slide và không coi lời chào như “hello” là yêu cầu tra
  cứu kiến thức.
- Pull, so sánh và test các nhánh trước khi tích hợp vào `develop`.

## AI hỗ trợ tôi ở đâu

Tôi dùng AI agent để đọc repo, lọc chatlog, gợi ý test case, sửa code và chạy lại
eval. Tôi không dùng kết quả AI làm kết luận ngay. Sau mỗi lượt, tôi đọc lại từng
response, đối chiếu citation với slide và lưu report theo phiên bản. Backend hiện
có 92 test đạt; lượt eval gần nhất đạt 25/31 và không còn lỗi critical.

## Failure khiến tôi đổi cách làm

Golden set v2 từng đạt 23/23, nhưng câu hỏi và cách chấm bám quá sát code nên kết
quả này không phản ánh cách người dùng thật đặt câu hỏi. Khi chuyển sang v3, kết
quả đầu chỉ còn 16/31 và có 6 lỗi critical.

Sau đó tôi giữ bộ test theo version, bổ sung câu paraphrase và câu từ quan sát thật,
đồng thời đọc thủ công cả các case fail. Bài học của tôi là điểm cao không có nhiều
ý nghĩa nếu test được viết theo đúng những gì code đang làm.

## Nếu có thêm một tuần

- Ưu tiên cải thiện citation grounding, hiện mới đạt 70,59% so với chuẩn 90%.
- Giảm P90 latency từ 18,5 giây xuống dưới 12 giây bằng retrieval và rerank tốt hơn.
