# Reflection - Nguyễn Chí Hiếu

- Mã học viên: `2A202601931`
- GitHub: `Hieunc2910`
- Phần phụ trách: phân tích dữ liệu, thiết kế golden set và evaluator,
  grounding/citation, tài liệu dự án và tích hợp các nhánh.

## 1. Phần tôi trực tiếp làm

Tôi bắt đầu từ dữ liệu mẫu của VLearn thay vì đi thẳng vào code. Tôi đọc cấu trúc
chatlog, tách các lượt của Tutor và đếm những tình huống liên quan đến nhu cầu tóm
tắt hoặc tổng hợp học liệu. Kết quả cho thấy trong 1.261 lượt hỏi đáp có 156 lượt
thuộc nhóm này; 87/156 lượt nhận phản hồi theo kiểu không truy cập được hoặc không
tìm thấy nội dung, còn 101/156 lượt không có citation. Con số tổng thể cũng đáng
chú ý: 582/1.261 lượt Tutor trả lời mà không kèm số trang. Phần phân tích và cách
đếm được lưu tại
[`data-analysis-vlearn-context.md`](../codebase/docs/data-analysis-vlearn-context.md).

Từ các pain quan sát được, tôi cùng nhóm chuyển ý tưởng ban đầu thành VLearn Smart
Contextual Companion. AI trong sản phẩm không chỉ sinh câu trả lời. Nó phải xác
định câu hỏi đang cần phạm vi nào, tìm đúng học liệu, rồi mới quyết định trả lời
từ slide, bổ sung nguồn ngoài, hỏi lại hay chuyển TA. Tôi phụ trách biến yêu cầu
này thành bộ câu thử có thể đo được.

Tôi xây golden set theo nhiều phiên bản. Bản v2 có các ca theo trang hiện tại,
cả tài liệu, cả buổi, nguồn ngoài, câu mơ hồ và câu phải từ chối. Sau đó tôi tạo
v3 với 31 câu, trong đó có 10 câu bắt nguồn từ quan sát thực tế. Tôi chủ động thêm
câu viết sai chính tả, câu cụt, câu trộn tiếng Anh, paraphrase và những yêu cầu có
thể gây hậu quả như hỏi deadline hoặc xin đáp án. Tôi cũng chỉnh evaluator để
không chỉ kiểm tra nhãn scope mà còn kiểm tra hành vi người dùng nhìn thấy, citation
và các lỗi critical.

Ngoài phần eval, tôi tham gia sửa luồng grounding. Một citation chỉ được hiển thị
khi backend thực sự trả về nguồn đã dùng; trường hợp model không tạo được câu trả
lời thì UI không được gắn citation cho có. Với câu hỏi ngoài slide, hệ thống có
thể dùng nguồn web, nhưng nguồn đó phải đi qua metadata riêng để không bị trình
bày như một slide của khóa học. Tôi cũng sửa trường hợp lời chào như “hello” bị
coi là câu hỏi kiến thức và bị đẩy sang tra cứu web. Các thay đổi này có thể đối
chiếu ở các commit `8e81b31`, `34f30b7` và `42108a3`.

Tôi còn làm phần tích hợp: kéo thay đổi mới từ `develop`, so sánh các nhánh, chạy
test trước khi giữ hoặc bỏ một hướng sửa, rồi đưa cấu trúc repo về đúng format bài
nộp. Tôi có thể giải thích các artifact do mình phụ trách, gồm
[`golden_set_v3.json`](../eval/golden_set_v3.json),
[`EVAL_REPORT_V3.md`](../eval/EVAL_REPORT_V3.md) và
[`MANUAL_REVIEW_V3.md`](../eval/MANUAL_REVIEW_V3.md).

## 2. AI đã hỗ trợ tôi như thế nào

Tôi dùng AI agent khá nhiều để đọc repo, tìm các trường liên quan trong chatlog,
đề xuất nhóm test, viết script chấm và thử các bản sửa backend. Phần có ích nhất
là AI có thể rà nhiều file và chạy lại cùng một bộ test rất nhanh. Trong thời gian
hackathon, tốc độ đó giúp tôi kiểm tra một giả thuyết bằng số liệu trước khi nhóm
đầu tư vào nó.

Nhưng tôi không lấy kết quả AI tạo ra làm kết luận cuối. Khi AI đề xuất test case,
tôi đối chiếu lại với chatlog và giữ riêng trường `source` hoặc `observation` để
biết câu nào có nguồn thực tế. Khi AI sửa scorer, tôi đọc từng kết quả pass/fail
và kiểm tra cả câu trả lời thực tế, vì một scorer sai có thể làm phiên bản mới
trông tốt hơn mà sản phẩm không hề tốt hơn. Tôi chạy full golden set qua NVIDIA
API, lưu report theo phiên bản, rồi audit thủ công từng response trong v3.

Cách kiểm tra này đã phát hiện khác biệt giữa “citation thuộc danh sách nguồn”
và “citation thật sự chứng minh cho claim”. Một câu trả lời có thể trỏ đúng slide
nhưng nội dung vẫn suy diễn quá phần slide nói. Vì vậy ở v3 tôi dùng thêm tiêu chí
claim-level grounding, thay vì chỉ kiểm tra số trang có nằm trong tập kết quả
retrieval hay không.

Tôi cũng luôn chạy test backend và thử trực tiếp trên UI sau các thay đổi liên quan
đến routing hoặc citation. Ở trạng thái mới nhất, backend có 92 test đạt. Lượt eval
được lưu đạt 25/31, decision pass 96,77% và không còn lỗi critical. Dù vậy, citation
grounding mới đạt 70,59% và P90 latency là 18,5 giây. Tôi giữ nguyên hai con số chưa
đạt này trong tài liệu vì đó mới là trạng thái thật của sản phẩm.

## 3. Một lần tôi phải đổi cách làm

Lần khiến tôi thay đổi nhiều nhất là khi v2 đạt 23/23. Ban đầu đây có vẻ là kết quả
rất tốt. Đọc kỹ từng case, tôi nhận ra bộ câu hỏi và scorer đang bám quá sát vào
cách code hiện tại hoạt động. Câu hỏi ngắn, từ khóa rõ, còn expected output kiểm
tra đúng những trường mà pipeline vốn đã sinh ra. Bộ test lúc đó chứng minh code
hợp với chính bộ test của nó, chưa chứng minh sản phẩm xử lý được cách học viên
thật sự đặt câu hỏi.

Tôi tạo v3 để cố tình làm hệ thống khó xử hơn. Kết quả lần đầu chỉ đạt 16/31 và có
6 lỗi critical. Có case hỏi deadline bị trả lời như thể thông tin có trong slide,
case mơ hồ bị đoán, và citation làm câu trả lời sai trông đáng tin hơn. Sau đó tôi
đọc từng câu hỏi cùng response thay vì chỉ nhìn tổng điểm. Việc này giúp tách lỗi
định tuyến, lỗi retrieval, lỗi sinh câu trả lời và lỗi của chính evaluator.

Từ đó tôi không xem tỷ lệ pass cao là mục tiêu duy nhất. Golden set phải có lịch
sử phiên bản, có ca quan sát thực tế, có câu paraphrase và phải giữ lại cả các dòng
fail. Với lỗi nguy hiểm, nhóm dùng thêm hard safety gate: khi câu hỏi không được
phép trả lời hoặc không có căn cứ thì hệ thống không được sinh câu trả lời có
citation. Bản mới nhất đã đưa lỗi critical về 0, nhưng các chỉ số còn thiếu vẫn
được ghi rõ thay vì đổi chuẩn cho dễ đạt.

## 4. Nếu có thêm một tuần

Tôi sẽ ưu tiên citation grounding trước. Routing hiện đã khá ổn, nhưng citation
grounding 70,59% vẫn thấp hơn chuẩn 90%. Đây là phần liên quan trực tiếp đến lời
hứa của sản phẩm: giúp người học kiểm tra được câu trả lời nằm ở đâu, chứ không chỉ
đưa ra một số trang nhìn có vẻ hợp lý. Tôi sẽ tách câu trả lời thành các claim,
đối chiếu từng claim với excerpt được retrieval và loại citation không hỗ trợ
trực tiếp cho nội dung đó.

Sau đó tôi sẽ xử lý latency ở các yêu cầu phạm vi rộng. P90 18,5 giây là quá lâu
cho một thao tác hỏi đáp. Hướng tôi muốn thử là retrieval hai bước: chọn slide ứng
viên trước, rerank một tập nhỏ rồi mới gửi context cho model. Cách này cần đo cùng
grounding, vì cắt context đơn thuần có thể nhanh hơn nhưng lại bỏ mất slide cần
thiết.

Cuối cùng là user validation. Thư mục `validation/` hiện chưa có đủ 5 lượt thử thật.
Đây là khoảng trống mà thêm test tự động không bù được. Tôi muốn quan sát học viên
tự đặt câu hỏi trên một bộ slide, xem họ có mở citation để kiểm tra không, và ghi
lại nguyên văn chỗ họ vẫn thấy Tutor trả lời khó hiểu. Những phản hồi đó sẽ là đầu
vào cho golden set tiếp theo, thay vì tiếp tục tự nghĩ câu hỏi trong nhóm.
