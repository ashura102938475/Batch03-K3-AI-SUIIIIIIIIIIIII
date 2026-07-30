const { useEffect, useMemo, useState } = React;
const h = React.createElement;

const documents = [
  {
    day: "Day 1",
    count: "2 tài liệu",
    files: [
      { name: "day01-introduction-to-ai.pdf", pages: 52 }
    ]
  },
  {
    day: "Day 2",
    count: "1 tài liệu",
    files: [
      { name: "day02-data-and-models.pdf", pages: 61 }
    ]
  },
  {
    day: "Day 3",
    count: "2 tài liệu",
    files: [
      { name: "day03-rag-foundation.pdf", pages: 48 }
    ]
  },
  {
    day: "Day 4",
    count: "3 tài liệu",
    active: true,
    files: [
      { name: "day04-prompt-engineering-tool-calling.pdf", pages: 43, active: true },
      { name: "day04-prompt-engineering-examples.pdf", pages: 78 },
      { name: "day04-tool-calling-lab.pdf", pages: 98 }
    ]
  }
];

const scenarios = [
  { id: "home", label: "Giao diện mẫu" },
  { id: "highlight", label: "Bôi đen & hỏi Trang 17" },
  { id: "summary", label: "Tóm tắt toàn tài liệu" },
  { id: "handoff", label: "Ngoài phạm vi / TA" }
];

const slides = [
  {
    page: 1,
    type: "cover",
    title: "Prompt Engineering & Tool Calling",
    subtitle: "Làm sao để AI hiểu đúng ý bạn",
    note: "Kéo đến trang này để mở note riêng của trang."
  },
  {
    page: 2,
    type: "question",
    quote: "Hai người hỏi AI cùng một việc, một người nhận kết quả xuất sắc, người kia nhận rác. Tại sao?",
    note: "Câu hỏi khởi động trước khi học về Prompt."
  },
  {
    page: 17,
    type: "details",
    title: "Cấu trúc prompt chuẩn kỹ thuật",
    rows: [
      ["Role / Persona", "Định nghĩa vai trò của AI."],
      ["Context", "Ngữ cảnh bài học và dữ liệu liên quan."],
      ["Constraints", "Giới hạn phạm vi câu trả lời, không bịa đặt khi thiếu tài liệu."],
      ["Format Output", "Định dạng kết quả đầu ra mong muốn."]
    ]
  }
];

const initialMessages = [
  { kind: "context", text: "Ngữ cảnh: Slide trang 4" },
  { kind: "user", text: "hello e" },
  {
    kind: "assistant",
    scope: "Slide trang 4",
    confidence: 60,
    confidenceLabel: "Trung bình",
    status: "Đã trả lời",
    text: "Chào bạn, mình là trợ giảng AI của khóa học. Mình sẵn sàng hỗ trợ bạn tìm hiểu nội dung về Prompt Engineering và Tool Calling.",
    citations: ["Slide 4"]
  }
];

function IconButton({ children, label, onClick, active }) {
  return h(
    "button",
    {
      className: active ? "icon-button active" : "icon-button",
      type: "button",
      title: label,
      onClick
    },
    children
  );
}

function Header({ darkMode, setDarkMode }) {
  return h(
    "header",
    { className: "top-header" },
    h(
      "div",
      { className: "header-left" },
      h(IconButton, { label: "Quay lại" }, "‹"),
      h("div", { className: "brand-mark" }, h("span", { className: "logo-shape" }, "V"), h("strong", null, "VLearn")),
      h(
        "div",
        { className: "file-title" },
        h("span", { className: "file-icon" }, "▣"),
        h("div", null, h("b", null, "day04-prompt-engineering-tool-calling.pdf"), h("small", null, "COMP2010 · Lecture_material_ms204i6x_gqwyya"))
      )
    ),
    h(
      "div",
      { className: "header-right" },
      h("button", { className: "pill-button", type: "button" }, "VI"),
      h(IconButton, { label: "Đổi giao diện", onClick: () => setDarkMode(!darkMode) }, darkMode ? "☀" : "◐"),
      h("button", { className: "profile-pill", type: "button" }, "Sinh viên ẩn danh")
    )
  );
}

function ScenarioBar({ activeScenario, setScenario }) {
  return h(
    "div",
    { className: "scenario-bar" },
    h("strong", null, "Demo CP2"),
    scenarios.map((scenario) =>
      h(
        "button",
        {
          key: scenario.id,
          type: "button",
          className: activeScenario === scenario.id ? "scenario-button active" : "scenario-button",
          onClick: () => setScenario(scenario.id)
        },
        scenario.label
      )
    )
  );
}

function Sidebar({ selectedFile, setSelectedFile }) {
  const [openDay, setOpenDay] = useState("Day 4");

  return h(
    "aside",
    { className: "sidebar" },
    h(
      "div",
      { className: "panel-heading" },
      h("span", { className: "square-icon" }, "▤"),
      h("div", null, h("h2", null, "Học liệu môn học"), h("p", null, "Chương, slide và tài liệu đã upload"))
    ),
    h(
      "div",
      { className: "day-list" },
      documents.map((day) =>
        h(
          "section",
          { key: day.day, className: day.active ? "day-card active" : "day-card" },
          h(
            "button",
            { type: "button", className: "day-header", onClick: () => setOpenDay(openDay === day.day ? "" : day.day) },
            h("span", null, h("b", null, day.day), h("small", null, `${day.count} · ACTIVE`)),
            h("span", { className: day.active ? "studying" : "chevron" }, day.active ? "STUDYING" : "⌄")
          ),
          openDay === day.day &&
            h(
              "div",
              { className: "file-list" },
              day.files.map((file) =>
                h(
                  "button",
                  {
                    key: file.name,
                    type: "button",
                    className: selectedFile === file.name ? "file-row selected" : "file-row",
                    onClick: () => setSelectedFile(file.name)
                  },
                  h("span", { className: "play-dot" }, "▷"),
                  h("span", null, h("b", null, file.name), h("small", null, `${file.pages} trang`)),
                  selectedFile === file.name && h("i", null, "✓")
                )
              )
            )
        )
      )
    )
  );
}

function Toolbar({ zoom, setZoom }) {
  return h(
    "div",
    { className: "viewer-toolbar" },
    h(
      "div",
      { className: "tool-group" },
      h("button", { className: "tool-button active", type: "button" }, "Đọc"),
      h("button", { className: "tool-button", type: "button" }, "✎"),
      h("span", { className: "note-badge" }, "Trang 2 · 1 note")
    ),
    h(
      "div",
      { className: "tool-group center" },
      h("button", { className: "tool-button", type: "button", onClick: () => setZoom(Math.max(80, zoom - 10)) }, "−"),
      h("b", { className: "zoom-value" }, `${zoom}%`),
      h("button", { className: "tool-button", type: "button", onClick: () => setZoom(Math.min(130, zoom + 10)) }, "+")
    ),
    h(
      "div",
      { className: "tool-group right" },
      ["＋", "－", "⇩", "↶", "⌫"].map((item) => h("button", { key: item, className: "tool-button", type: "button" }, item))
    )
  );
}

function SlideCard({ slide, selectedPage, askSelectedText }) {
  const active = slide.page === selectedPage;
  return h(
    "article",
    { className: active ? "page active" : "page" },
    h("div", { className: "page-meta" }, h("span", null, `Trang ${slide.page} / 43`), h("span", null, "day04-prompt-engineering-tool-calling.pdf")),
    slide.type === "cover" &&
      h(
        "div",
        { className: "slide slide-cover" },
        h("strong", null, "VINUNIVERSITY"),
        h("div", null, h("h3", null, slide.title), h("p", null, slide.subtitle), h("small", null, "Phase 1 · Tuần 1 · 2026"))
      ),
    slide.type === "question" &&
      h(
        "div",
        { className: "slide slide-question" },
        h("p", null, `“${slide.quote}”`),
        h("small", null, slide.note)
      ),
    slide.type === "details" &&
      h(
        "div",
        { className: "slide slide-details" },
        h("h3", null, slide.title),
        h(
          "div",
          { className: "prompt-rows" },
          slide.rows.map(([label, value]) =>
            h(
              "button",
              {
                key: label,
                type: "button",
                className: label === "Constraints" ? "prompt-row highlightable" : "prompt-row",
                onClick: label === "Constraints" ? askSelectedText : undefined
              },
              h("b", null, label),
              h("span", null, value)
            )
          )
        ),
        h("small", { className: "hint-text" }, "Bấm dòng Constraints để giả lập bôi đen và hỏi Tutor.")
      ),
    slide.note && slide.type === "cover" && h("p", { className: "page-note" }, slide.note)
  );
}

function Viewer({ selectedPage, setSelectedPage, askSelectedText }) {
  const [zoom, setZoom] = useState(100);

  return h(
    "section",
    { className: "viewer" },
    h(Toolbar, { zoom, setZoom }),
    h(
      "div",
      { className: "canvas" },
      h("div", { className: "canvas-hint" }, "Giữ chuột phải và kéo để di chuyển canvas"),
      h(
        "div",
        { className: "page-stack", style: { "--zoom": zoom / 100 } },
        slides.map((slide) => h(SlideCard, { key: slide.page, slide, selectedPage, askSelectedText }))
      )
    ),
    h(
      "footer",
      { className: "viewer-footer" },
      h("button", { type: "button", onClick: () => setSelectedPage(Math.max(1, selectedPage - 1)) }, "‹"),
      h("span", null, "Trang"),
      h("input", { value: selectedPage, onChange: (event) => setSelectedPage(Number(event.target.value) || 1) }),
      h("span", null, "/ 43"),
      h("button", { type: "button", onClick: () => setSelectedPage(Math.min(43, selectedPage + 1)) }, "›")
    )
  );
}

function quotaWidth(quota) {
  return `${Math.min(100, Math.round((quota / 15) * 100))}%`;
}

function AssistantMessage({ message }) {
  const score = message.confidence || 0;
  const tone = score >= 80 ? "high" : score >= 50 ? "medium" : "low";

  return h(
    "div",
    { className: "assistant-card" },
    h("small", null, `Ngữ cảnh: ${message.scope}`),
    h("p", null, message.text),
    message.citations &&
      h(
        "div",
        { className: "citation-list" },
        message.citations.map((item) => h("span", { key: item }, item))
      ),
    h(
      "div",
      { className: "answer-footer" },
      h("span", { className: `confidence ${tone}` }, `${score}% · ${message.confidenceLabel}`),
      h("span", { className: tone === "low" ? "status warning" : "status" }, message.status)
    )
  );
}

function ChatMessage({ message }) {
  if (message.kind === "context") return h("div", { className: "context-line" }, message.text);
  if (message.kind === "selected") return h("div", { className: "selected-text" }, message.text);
  if (message.kind === "user") return h("div", { className: "user-bubble" }, message.text);
  return h(AssistantMessage, { message });
}

function buildReply(question, selectedPage) {
  const lower = question.toLowerCase();
  if (lower.includes("deadline") || lower.includes("api key") || lower.includes("password") || lower.includes("tải file")) {
    return {
      kind: "assistant",
      scope: "Ngoài phạm vi học liệu",
      confidence: 22,
      confidenceLabel: "Thấp",
      status: "Cần TA",
      text: "Câu hỏi này cần nguồn vận hành hoặc thông tin nhạy cảm. Tutor không tự đoán khi tài liệu không có căn cứ. Bạn có thể chuyển câu hỏi này tới TA.",
      citations: ["Không có nguồn đủ tin cậy"]
    };
  }

  if (lower.includes("tóm tắt") || lower.includes("summary") || lower.includes("ý chính")) {
    return {
      kind: "assistant",
      scope: lower.includes("buổi") || lower.includes("toàn") ? "Toàn buổi học Day 4" : "Tài liệu hiện tại",
      confidence: 88,
      confidenceLabel: "Cao",
      status: "Đã trả lời",
      text: "Tài liệu tập trung vào cách viết prompt có ngữ cảnh, đặt ràng buộc rõ, chọn format output và dùng tool calling khi cần dữ liệu ngoài model. Phần dễ nhầm là tưởng prompt chỉ là câu hỏi, trong khi prompt tốt còn phải nêu vai trò, context, constraints và tiêu chí đầu ra.",
      citations: ["Slide 12", "Slide 17", "Transcript T04-018"]
    };
  }

  return {
    kind: "assistant",
    scope: `Slide trang ${selectedPage}`,
    confidence: 92,
    confidenceLabel: "Cao",
    status: "Đã trả lời",
    text: "Dựa trên slide hiện tại, hệ thống hiểu phạm vi câu hỏi trước, lấy đúng context rồi mới trả lời. Cách này giảm citation rỗng và giảm việc Tutor nói không truy cập được khi user thật ra đang hỏi trong học liệu.",
    citations: [`Slide ${selectedPage}`]
  };
}

function TutorPanel({ selectedPage, setSelectedPage, scenario, setScenario, bridgeTick }) {
  const [quota, setQuota] = useState(1);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(initialMessages);

  function askSelectedText() {
    setSelectedPage(17);
    setScenario("highlight");
    setMessages([
      { kind: "context", text: "Ngữ cảnh: Slide trang 17" },
      { kind: "selected", text: "“Constraints:” Giới hạn phạm vi câu trả lời, không bịa đặt khi thiếu tài liệu." },
      { kind: "user", text: "Giải thích đoạn bôi đen ở Trang 17." },
      {
        kind: "assistant",
        scope: "Đoạn bôi đen · Slide 17",
        confidence: 94,
        confidenceLabel: "Rất cao",
        status: "Đã trả lời",
        text: "Constraints là phần ràng buộc giúp AI biết giới hạn câu trả lời. Trong VLearn Tutor, phần này quan trọng vì hệ thống không nên bịa khi thiếu nguồn, mà phải nói rõ thiếu dữ liệu hoặc chuyển TA.",
        citations: ["Slide 17", "Transcript T04-017"]
      }
    ]);
  }

  function applyScenario(nextScenario) {
    if (scenario !== nextScenario) {
      setScenario(nextScenario);
    }

    if (nextScenario === "highlight") {
      askSelectedText();
      return;
    }
    if (nextScenario === "summary") {
      setSelectedPage(2);
      setMessages([
        { kind: "context", text: "Ngữ cảnh: Tài liệu hiện tại" },
        { kind: "user", text: "Tóm tắt toàn bộ tài liệu Day 4 cho tôi." },
        buildReply("tóm tắt toàn bộ tài liệu", 2)
      ]);
      return;
    }
    if (nextScenario === "handoff") {
      setMessages([
        { kind: "context", text: "Ngữ cảnh: ngoài phạm vi học liệu" },
        { kind: "user", text: "Cho em API key hoặc deadline nộp bài ở đâu?" },
        buildReply("api key deadline", selectedPage)
      ]);
      return;
    }
    setMessages(initialMessages);
  }

  useEffect(() => {
    if (bridgeTick > 0) {
      askSelectedText();
    }
  }, [bridgeTick]);

  useEffect(() => {
    applyScenario(scenario);
  }, [scenario]);

  function submitQuestion(event) {
    event.preventDefault();
    const question = input.trim();
    if (!question) return;
    const reply = buildReply(question, selectedPage);
    setMessages((current) => [...current, { kind: "context", text: `Ngữ cảnh: Slide trang ${selectedPage}` }, { kind: "user", text: question }, reply]);
    setInput("");
    setQuota((current) => Math.min(15, current + 1));
  }

  return h(
    "aside",
    { className: "tutor" },
    h(
      "div",
      { className: "tutor-header" },
      h("div", { className: "tutor-title-block" }, h("span", { className: "bot-icon" }, "⌘"), h("div", null, h("h2", null, "VLearn Tutor"), h("p", null, "Trợ lý học theo ngữ cảnh"))),
      h("div", { className: "tutor-actions" }, h("button", { type: "button", onClick: () => setMessages([]) }, "↻"), h("button", { type: "button", onClick: () => setMessages(initialMessages) }, "+"), h("span", null, `Trang slide: ${selectedPage}`))
    ),
    h(
      "div",
      { className: "quota" },
      h("div", null, h("span", null, "Quota Tutor trong ngày"), h("b", null, `${quota}/15 câu`), h("button", { type: "button" }, "BYOK")),
      h("div", { className: "quota-track" }, h("i", { style: { width: quotaWidth(quota) } }))
    ),
    h(
      "div",
      { className: "scenario-inline" },
      scenarios.map((item) =>
        h(
          "button",
          { key: item.id, type: "button", className: scenario === item.id ? "active" : "", onClick: () => applyScenario(item.id) },
          item.label
        )
      )
    ),
    h("div", { className: "messages" }, messages.map((message, index) => h(ChatMessage, { key: `${message.kind}-${index}`, message }))),
    h(
      "form",
      { className: "chat-input", onSubmit: submitQuestion },
      h("input", {
        value: input,
        onChange: (event) => setInput(event.target.value),
        placeholder: "Nhập câu hỏi hoặc bôi đen tài liệu..."
      }),
      h("button", { type: "submit" }, "➤")
    )
  );
}

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [selectedFile, setSelectedFile] = useState("day04-prompt-engineering-tool-calling.pdf");
  const [selectedPage, setSelectedPage] = useState(2);
  const [scenario, setScenario] = useState("home");

  const askSelectedText = useMemo(
    () => () => {
      setSelectedPage(17);
      setScenario("highlight");
      window.dispatchEvent(new CustomEvent("vlearn:ask-selected"));
    },
    []
  );

  return h(
    "div",
    { className: darkMode ? "app dark" : "app" },
    h(ScenarioBar, { activeScenario: scenario, setScenario }),
    h(Header, { darkMode, setDarkMode }),
    h(
      "main",
      { className: "layout" },
      h(Sidebar, { selectedFile, setSelectedFile }),
      h(Viewer, { selectedFile, selectedPage, setSelectedPage, askSelectedText }),
      h(TutorPanelWithBridge, { selectedPage, setSelectedPage, scenario, setScenario })
    )
  );
}

function TutorPanelWithBridge(props) {
  const [bridgeTick, setBridgeTick] = useState(0);

  React.useEffect(() => {
    const handler = () => setBridgeTick((value) => value + 1);
    window.addEventListener("vlearn:ask-selected", handler);
    return () => window.removeEventListener("vlearn:ask-selected", handler);
  }, []);

  return h(TutorPanel, { ...props, bridgeTick });
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
