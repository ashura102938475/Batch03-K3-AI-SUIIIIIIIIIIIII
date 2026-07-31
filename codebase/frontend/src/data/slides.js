const dayOnePdfUrl = new URL("../../../data/vlearn-pack/slides/d1-slide-hackathon.pdf", import.meta.url).href;
const dayTwoPdfUrl = new URL("../../../data/vlearn-pack/slides/d2-slide-hackathon.pdf", import.meta.url).href;

export const evidenceMetrics = {
  summaryRate: "12.4%",
  noAccessRate: "55.8%",
  globalEmptyCitationRate: "46.2%"
};

export const transcriptSnippets = [
  {
    id: "T04-003",
    dayId: "day01",
    title: "Khoá đi sâu vào LLM",
    text: "Buổi học nền tảng giải thích vì sao ChatGPT, Gemini, Claude làm được nhiều việc và khoá học đi sâu vào LLM, công cụ và agent."
  },
  {
    id: "T04-013",
    dayId: "day01",
    title: "Nội dung ngày học",
    text: "Ngày học đi qua bức tranh AI, lịch sử AI, cơ chế vận hành của LLM, mổ xẻ mô hình và gọi API lần đầu."
  },
  {
    id: "T01-006",
    dayId: "day02",
    title: "Bóc tách yêu cầu mơ hồ",
    text: "Khi đề bài mơ hồ, người làm sản phẩm cần biến nó thành vài lựa chọn cụ thể và xác minh lại với stakeholder."
  },
  {
    id: "T02-020",
    dayId: "day02",
    title: "Chọn mức tự động hoá",
    text: "Automation cần chọn theo hậu quả khi sai: rule/script cho logic ổn định, workflow cho chuỗi bước, agent cho việc cần tự lập kế hoạch."
  }
];

const dayOneSlides = [
  ["AI & LLM Foundation", "Bạn đang dùng AI mỗi ngày - nhưng thực sự bên trong nó đang làm gì?", ["Mở đầu buổi Foundation", "Định vị mục tiêu học LLM", "Bối cảnh AI thực chiến"]],
  ["Agenda", "Bức tranh AI, lịch sử 70 năm, bên trong LLM, từ LLM đến agent, model landscape, token cost và gọi API.", ["Bức tranh AI và các tầng AI", "Cơ chế vận hành của LLM", "Chọn model và chi phí token"]],
  ["AI, ML, Deep Learning, GenAI, LLM", "AI là chiếc ô lớn; LLM là model nền chuyên ngôn ngữ và là tầng nền của nhiều trải nghiệm AI hiện nay.", ["AI bao phủ các hệ thống thông minh", "Machine learning học từ dữ liệu", "LLM là lõi của chatbot hiện đại"]],
  ["Ba nhóm AI chính", "Discriminative AI dự đoán nhãn, Generative AI sinh nội dung mới, Agentic AI nhận mục tiêu rồi tự làm nhiều bước.", ["Input -> nhãn hoặc con số", "Prompt -> nội dung mới", "Goal -> plan -> action"]],
  ["Lịch sử AI 70 năm", "AI đi qua khai sinh, hai mùa đông, model đơn lẻ và các hệ thống có khả năng hành động.", ["1956 là mốc khai sinh AI", "Hai mùa đông vì kỳ vọng vượt năng lực", "System hiện đại kết hợp nhiều thành phần"]],
  ["Expert System", "Hệ chuyên gia đặt lại câu hỏi: nếu AI chỉ giải thật tốt một loại bài toán chuyên môn hẹp thì sao?", ["Thu hẹp phạm vi bài toán", "Dựa trên luật và tri thức chuyên gia", "Dễ chạm trần khi bối cảnh thay đổi"]],
  ["ImageNet và dữ liệu", "Fei-Fei Li chọn xây bộ dữ liệu thay vì chỉ chạy theo thuật toán thông minh hơn.", ["Dữ liệu chất lượng mở khoá deep learning", "Label thủ công tạo nền móng", "Bài học: dữ liệu thường quyết định thành công"]],
  ["Transformer", "Transformer cho mô hình hiểu ngôn ngữ linh hoạt hơn vì mỗi token có thể nhìn sang các token quan trọng khác.", ["Attention thay đổi cách xử lý chuỗi", "Bối cảnh được cân nhắc động", "Nền móng cho LLM hiện đại"]],
  ["ChatGPT", "ChatGPT khiến người dùng phổ thông trực tiếp chạm vào năng lực LLM qua hội thoại.", ["Hạ rào cản sử dụng AI", "Tạo kỳ vọng mới về chatbot", "Đưa GenAI vào thói quen hằng ngày"]],
  ["LLM là gì?", "Một model nền có thể đứng sau chatbot, tóm tắt tài liệu, viết code, dịch và phân tích.", ["Không chỉ là chatbot", "Một năng lực dùng cho nhiều việc", "Thay đổi cách build sản phẩm"]],
  ["Đầu ra là phân bố xác suất", "Với mọi ngữ cảnh, model chấm điểm nhiều token trong từ vựng rồi chọn token tiếp theo.", ["Không truy xuất sự thật tuyệt đối", "Sinh theo xác suất", "Cần grounding khi dùng cho học liệu"]],
  ["Sinh văn bản", "Mỗi token mới được nối vào ngữ cảnh, rồi mô hình chạy tiếp vòng lặp predict.", ["Sinh từng token", "Ngữ cảnh thay đổi sau mỗi bước", "Câu trả lời trôi chảy không đồng nghĩa đúng"]],
  ["Token", "Model không đọc từ nguyên vẹn mà cắt văn bản thành các mảnh nhỏ gọi là token.", ["Chi phí tính theo token", "Tiếng Việt có thể tốn token hơn", "Prompt dài làm chậm và tốn hơn"]],
  ["Context", "Mỗi lần trả lời, model chỉ nhìn được lượng chữ hữu hạn trong context window.", ["Không có trong context thì model không thấy", "Cần đưa tài liệu vào prompt", "Context quá dài dễ mất trọng tâm"]],
  ["Attention", "Attention cho phép mỗi token nhìn sang các token quan trọng khác.", ["Liên kết ý trong câu", "Giúp xử lý phụ thuộc xa", "Vẫn cần dữ liệu đúng trong context"]],
  ["Quản lý prompt", "Đầu và cuối prompt thường được chú ý nhiều hơn; yêu cầu quan trọng không nên bị chôn giữa prompt.", ["Đưa nhiệm vụ chính lên rõ", "Tách dữ liệu khỏi chỉ thị", "Giảm nhiễu trong prompt"]],
  ["Dense và Mixture of Experts", "Một model dense cho mọi token đi qua toàn bộ khớp nối, MoE kích hoạt một phần chuyên gia.", ["Dense dùng toàn bộ tham số", "MoE kích hoạt chuyên gia", "Quy mô không nói hết chi phí"]],
  ["LLM được tạo ra như thế nào?", "Mô hình đi qua pre-training, instruction tuning, RLHF và luyện đề để thành trợ lý biết nghe lời.", ["Pre-training học ngôn ngữ", "Instruction tuning học làm theo lệnh", "RLHF uốn theo phản hồi"]],
  ["RLHF", "RLHF dùng phản hồi của con người để xếp hạng và điều chỉnh câu trả lời.", ["Model viết nhiều đáp án", "Con người xếp hạng", "Reward model hướng hành vi"]],
  ["Bong bóng thời gian", "Model bị đóng băng tại thời điểm ngừng đọc; chuyện sau đó cần được cung cấp thêm.", ["Không tự biết dữ kiện mới", "Cần nguồn cập nhật", "Không đoán deadline"]],
  ["Lỗi học từ tín hiệu sai", "Model có thể học tín hiệu bề mặt thay vì bản chất.", ["Cần hiểu failure mode", "Dữ liệu lệch tạo dự đoán lệch", "Không đánh giá bằng cảm tính"]],
  ["Suy luận cần nháp", "Không có nháp, model dễ trả lời ngay nhưng sai ở bài toán cần nhiều bước.", ["Tách bài toán thành bước", "Kiểm kết quả trung gian", "Đừng tin câu trôi chảy quá nhanh"]],
  ["Từ LLM đến agent", "Mỗi bậc thêm một năng lực: LLM trần, có dữ liệu mới, có công cụ, rồi lập kế hoạch nhiều bước.", ["LLM trần", "Thêm dữ liệu và tool", "Agent cần kiểm soát rủi ro"]],
  ["Giải phẫu agent", "Agent gồm mục tiêu, reasoning, tools, memory và guardrails trong một vòng lặp.", ["Goal định nghĩa việc cần đạt", "Tools giúp hành động", "Guardrails giữ hệ thống trong biên"]],
  ["Chi phí model giảm", "Cùng mức năng lực, chi phí model giảm nhanh theo thời gian.", ["Không chọn model theo hào quang", "Tối ưu tầng năng lực", "Theo dõi chi phí"]],
  ["Chọn model theo tầng", "Hai lỗi đối xứng là dùng frontier cho việc đơn giản hoặc model yếu cho việc khó.", ["Xác định yêu cầu task", "Chọn model đủ tốt", "Đo lại bằng eval"]],
  ["Token có giá", "Prompt, system instruction, context và lịch sử chat đều là input; câu trả lời là output.", ["Output thường đắt hơn input", "Context dài tăng chi phí", "Tóm tắt cần kiểm soát độ dài"]],
  ["Giải phẫu prompt", "Prompt gồm system instruction, task, context và output format.", ["System instruction đặt vai trò", "Context là dữ liệu nguồn", "Format giúp output dễ kiểm"]],
  ["Temperature và top_p", "Temperature và top_p điều chỉnh mức độ liều khi chọn token tiếp theo.", ["Temperature thấp ổn định hơn", "top_p giới hạn vùng xác suất", "Học liệu nên ưu tiên ổn định"]]
];

const dayTwoSlides = [
  ["Xác định bài toán cho AI", "Từ yêu cầu mơ hồ đến Problem Statement rõ ràng.", ["Đặt đúng vấn đề", "Không nhảy thẳng vào giải pháp", "Dùng AI như lựa chọn có kiểm chứng"]],
  ["Agenda", "Problem Discovery, Problem Statement, PAIR, automate/augment, success criteria, UX/HITL và lab nhóm.", ["Double Diamond và HCD", "Reward function", "Go / Not Yet / No-Go"]],
  ["Double Diamond", "Discover và Define giúp thu hẹp bài toán gốc trước khi Develop và Deliver giải pháp.", ["Giải đúng vấn đề", "Mở rộng quan sát", "Thu hẹp bằng bằng chứng"]],
  ["Discover", "Khám phá bằng quan sát thực tế, phỏng vấn người dùng, khảo sát và phân tích quy trình.", ["Observation", "User interview", "Workflow mining"]],
  ["Case Cursor", "Từ bỏ AI thiết kế CAD để tập trung vào AI code editor, nơi đội ngũ hiểu sâu workflow.", ["Chọn thị trường mình hiểu", "Giữ lợi thế cốt lõi", "Không chạy theo mọi cơ hội AI"]],
  ["Dấu hiệu bài toán tốt", "Bài toán nên có tác vụ lặp lại, tốn thời gian, bottleneck rõ và baseline đo được.", ["Tác vụ lặp lại", "Mất nhiều thời gian", "Có điểm nghẽn đo được"]],
  ["Bẫy solution-first", "Xây chatbot hoặc agent trước khi làm rõ quy trình vận hành dễ khiến nhóm giải sai việc.", ["Đừng bắt đầu bằng công nghệ", "Mô tả workflow hiện tại", "Định nghĩa pain cụ thể"]],
  ["PAIR - Reframe câu hỏi", "Thay 'có dùng AI được không' bằng 'giải quyết việc này thế nào' và 'AI có giải tốt hơn không'.", ["Không mặc định AI-first", "So với rule/heuristic", "Chọn AI khi có leverage thật"]],
  ["Bài toán một câu", "Problem statement cần nêu vấn đề cụ thể, đối tượng ảnh hưởng và workflow liên quan.", ["Không bao gồm giải pháp", "Nêu actor rõ", "Gắn với hành vi thật"]],
  ["Câu hỏi khám phá quy trình", "Cần hỏi quy trình hiện tại, điểm nghẽn, dữ liệu, ràng buộc và ai chịu hậu quả khi sai.", ["Quy trình hiện tại", "Nút thắt", "Sai thì ai chịu"]],
  ["Baseline và Target", "Thiết lập hiện trạng, mục tiêu và khoảng cách cần cải thiện bằng con số cụ thể.", ["Where we are", "Where to go", "Gap cần đóng"]],
  ["Output Metric", "Metric có thể là thời lượng quy trình, tỷ lệ sai sót, chất lượng đầu ra hoặc hài lòng.", ["Thời lượng giảm", "Tỷ lệ sai sót", "Chất lượng đầu ra"]],
  ["Giao điểm nhu cầu x thế mạnh AI", "Bài toán cần nằm trong nhóm việc AI làm tốt hơn rule hoặc heuristic.", ["Đọc hiểu ngôn ngữ", "Tổng hợp thông tin", "Xử lý đầu vào đa dạng"]],
  ["Pattern AI có thể giúp", "AI phù hợp với gợi ý cá nhân hoá, dự đoán, phân loại, tổng hợp và sinh nội dung.", ["Recommendation", "Prediction", "Summarization"]],
  ["Tính dự đoán được", "Các nút quen thuộc cần ổn định; trạng thái hệ thống cần rõ ràng.", ["Giữ điều khiển quen thuộc", "Hiện trạng thái", "Không làm user mất kiểm soát"]],
  ["Model - Context - Workflow", "Model xử lý ngôn ngữ; context cung cấp tri thức; workflow biến kết quả thành hành động.", ["Model không đủ nếu thiếu context", "Context cần đáng tin", "Workflow quyết định giá trị"]],
  ["Automate", "Chỉ chọn automate khi việc cần scale, user thiếu khả năng tự làm và kiểm soát được lỗi.", ["Sai sửa được không?", "Có người giám sát không?", "Có ranh giới vận hành không?"]],
  ["Cấp độ 1 - Rule / Script", "Dùng khi đầu vào ổn định, logic viết được bằng if/else và cần kết quả đúng 100%.", ["Đầu vào ít thay đổi", "Quy định rõ", "Không cần suy luận mở"]],
  ["Rule tĩnh", "Phù hợp cho FAQ, link thời khoá biểu, tài liệu sửa lỗi cơ bản và kịch bản rõ.", ["Rẻ và ổn định", "Dễ kiểm thử", "Không xử lý tốt câu mơ hồ"]],
  ["Prompt Chaining", "Chia task thành chuỗi LLM call tuần tự, có gate kiểm trước khi đi tiếp.", ["LLM Call -> Gate", "Gate fail -> Exit", "Kiểm từng bước"]],
  ["Cây quyết định cấp độ giải pháp", "Đi từ bài toán cốt lõi đến lựa chọn Rule, Workflow hay Agent.", ["Không dùng agent khi rule đủ", "Workflow cho nhiều bước", "Agent khi cần tự lập kế hoạch"]],
  ["Reward Function", "Reward function quyết định đâu là dự đoán đúng và định hình trải nghiệm người dùng.", ["Metric sai kéo hành vi sai", "Phản ánh giá trị thật", "Gắn hậu quả khi sai"]],
  ["Precision và Recall", "Precision cao tạo ít gợi ý nhưng chắc hơn; recall cao bắt nhiều case hơn nhưng tăng false positive.", ["Precision cao", "Recall cao", "Chọn theo cost-of-error"]],
  ["Template của PAIR", "Nếu chỉ số vượt/tụt khỏi ngưỡng có ý nghĩa, cần định nghĩa hành động tiếp theo.", ["Metric có threshold", "Có playbook khi fail", "Không đổi bar sau khi đo"]],
  ["Baseline - Evaluation", "So sánh AI với rule, nhân sự hoặc quy trình hiện tại; kiểm thử bằng case thật.", ["Baseline rõ", "Evaluation đủ case khó", "Chạy lại sau mỗi sửa"]],
  ["Input để build", "Cần Problem Statement đầy đủ và kịch bản kiểm thử trước khi build sâu.", ["Actor", "Workflow", "Bottleneck", "Boundary và HITL"]],
  ["6 yếu tố bài toán cốt lõi", "Một bài toán AI cần rõ actor, workflow, bottleneck, dữ liệu, boundary và metric.", ["Actor chịu ảnh hưởng", "Workflow hiện tại", "Metric kiểm chứng"]],
  ["Go / Not Yet / No-Go", "Go khi bài toán rõ, metric khả thi, AI phù hợp và kiểm soát được rủi ro.", ["Go", "Not Yet", "No-Go"]],
  ["Bài học cuối", "Brief mơ hồ không thể thay thế một Problem Statement hoàn chỉnh.", ["Không bỏ qua discovery", "Không đổi metric giữa chừng", "Giữ bằng chứng cho quyết định"]]
];

function toSlides(rows) {
  return rows.map(([title, body, bullets], index) => ({
    page: index + 1,
    title,
    kicker: index === 0 ? "AI IN ACTION" : "Slide data",
    body,
    bullets
  }));
}

export const dayGroups = [
  {
    dayId: "day01",
    dayLabel: "Day 1",
    subtitle: "1 TÀI LIỆU · ACTIVE",
    status: null,
    docs: [
      {
        id: "d1-slide-hackathon",
        dayId: "day01",
        dayLabel: "Day 1",
        filename: "d1-slide-hackathon.pdf",
        sourcePath: "codebase/data/vlearn-pack/slides/d1-slide-hackathon.pdf",
        pdfUrl: dayOnePdfUrl,
        title: "AI & LLM Foundation",
        pageCount: 29,
        accent: "blue",
        slides: toSlides(dayOneSlides)
      }
    ]
  },
  {
    dayId: "day02",
    dayLabel: "Day 2",
    subtitle: "1 TÀI LIỆU · ACTIVE",
    status: null,
    docs: [
      {
        id: "d2-slide-hackathon",
        dayId: "day02",
        dayLabel: "Day 2",
        filename: "d2-slide-hackathon.pdf",
        sourcePath: "codebase/data/vlearn-pack/slides/d2-slide-hackathon.pdf",
        pdfUrl: dayTwoPdfUrl,
        title: "Xác định bài toán cho AI",
        pageCount: 29,
        accent: "rose",
        slides: toSlides(dayTwoSlides)
      }
    ]
  }
];

export const documents = dayGroups.flatMap((group) => group.docs);
