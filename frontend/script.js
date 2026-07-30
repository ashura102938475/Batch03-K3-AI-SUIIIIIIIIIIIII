/* ==========================================================================
   VLearn Smart Contextual Companion - Interactive Script & Mock Data Engine
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const userMessageInput = document.getElementById("userMessageInput");
  const contextPillTag = document.getElementById("contextPillTag");
  const quotaCount = document.getElementById("quotaCount");
  const quotaFill = document.getElementById("quotaFill");
  const currentPageInput = document.getElementById("currentPageInput");
  const prevPageBtn = document.getElementById("prevPageBtn");
  const nextPageBtn = document.getElementById("nextPageBtn");
  const themeToggle = document.getElementById("themeToggle");
  const flowBtns = document.querySelectorAll(".flow-btn");
  const newChatBtn = document.getElementById("newChatBtn");
  const currentDocFilename = document.getElementById("currentDocFilename");

  let currentPage = 2;
  let totalPages = 43;
  let currentQuota = 1;
  const maxQuota = 15;
  let activeFlow = "screenshot";

  // ==========================================================================
  // MOCK DATA SCENARIOS
  // ==========================================================================

  const mockFlows = {
    // 1. Screenshot exact match flow
    screenshot: [
      { type: "context-tag", text: "Ngữ cảnh: Slide trang 17" },
      { type: "user-highlight", text: "“Constraints:”" },
      { type: "user-bubble", text: "Giải thích đoạn bôi đen ở Trang 17." },
      {
        type: "ai-card-error",
        meta: "Ngữ cảnh: slide trang 17",
        text: "AI hiện không thể trả lời. Vui lòng thử lại sau ít phút."
      },
      { type: "context-tag", text: "Ngữ cảnh: Slide trang 4" },
      { type: "user-bubble", text: "hello e" },
      {
        type: "ai-card-success",
        meta: "Ngữ cảnh: Slide trang 4",
        text: "Chào bạn, mình là trợ giảng AI của khoá học. Mình rất sẵn lòng hỗ trợ bạn trong việc tìm hiểu nội dung về Prompt Engineering và Tool Calling. Bạn có câu hỏi cụ thể nào về bài học ngày hôm nay không?",
        confidence: 60,
        confidenceText: "Trung bình",
        statusText: "ĐÃ TRẢ LỜI"
      }
    ],

    // 2. Highlight text flow
    highlight: [
      { type: "context-tag", text: "Ngữ cảnh: Slide trang 17" },
      { type: "user-highlight", text: "“Constraints:” Giới hạn phạm vi câu trả lời" },
      { type: "user-bubble", text: "Giải thích cho em đoạn Constraints này áp dụng thế nào?" },
      {
        type: "ai-card-success",
        meta: "Ngữ cảnh: Slide trang 17 · Citation [T04-017]",
        text: "Constraints (Ràng buộc) trong Prompt Engineering giúp giới hạn phạm vi suy luận của AI model. \n\n• Giúp AI không tự bịa đặt (Hallucination) khi không tìm thấy nguồn bài giảng.\n• Yêu cầu AI từ chối trả lời nếu câu hỏi nằm ngoài phạm vi tài liệu đã học.",
        confidence: 94,
        confidenceText: "Rất cao",
        statusText: "ĐÃ TRẢ LỜI"
      }
    ],

    // 3. AI Error flow
    "ai-error": [
      { type: "context-tag", text: "Ngữ cảnh: Slide trang 17" },
      { type: "user-bubble", text: "Tạo hộ mình đoạn code Python gọi Tool Calling." },
      {
        type: "ai-card-error",
        meta: "Ngữ cảnh: slide trang 17",
        text: "AI hiện không thể trả lời. Vui lòng thử lại sau ít phút."
      }
    ],

    // 4. High confidence flow
    "high-confidence": [
      { type: "context-tag", text: "Ngữ cảnh: Slide trang 12, 18" },
      { type: "user-bubble", text: "So sánh Prompt thông thường và Tool Calling?" },
      {
        type: "ai-card-success",
        meta: "Ngữ cảnh: Slide trang 12 & 18 · Citation [T04-012, T04-018]",
        text: "Dưới đây là so sánh giữa Prompt thông thường và Tool Calling:\n\n1. **Prompt thông thường**: Dựa hoàn toàn vào tri thức sẵn có của LLM, dễ bị hallucinate khi thông tin bị lỗi thời.\n2. **Tool Calling**: Cho phép LLM kết nối API/Database thực tế, truy xuất đúng context và thực thi các hành động động.",
        confidence: 92,
        confidenceText: "Cao",
        statusText: "ĐÃ TRẢ LỜI"
      }
    ],

    // 5. Out of scope flow
    "out-of-scope": [
      { type: "context-tag", text: "Ngữ cảnh: Hỏi đáp Logistics" },
      { type: "user-bubble", text: "Cho em hỏi hạn nộp bài tập Day 4 là mấy giờ ạ?" },
      {
        type: "ai-card-out-of-scope",
        meta: "Hệ thống phát hiện: Ngoài phạm vi học liệu",
        text: "Câu hỏi về deadline hoặc logistics cần xác minh từ kênh thông báo chính thức của khoá học. Prototype tuân thủ nguyên tắc không tự đoán thông tin nhạy cảm. Bạn có muốn chuyển câu hỏi này tới TA không?",
        confidence: 20,
        confidenceText: "Thấp",
        statusText: "CẦN HỖ TRỢ TA"
      }
    ]
  };

  // ==========================================================================
  // CHAT RENDER ENGINE
  // ==========================================================================

  function renderMessages(messages) {
    chatMessages.innerHTML = "";
    messages.forEach((msg) => {
      if (msg.type === "context-tag") {
        const tag = document.createElement("div");
        tag.className = "msg-context-tag";
        tag.textContent = msg.text;
        chatMessages.appendChild(tag);
      } else if (msg.type === "user-highlight") {
        const hl = document.createElement("div");
        hl.className = "msg-user-highlight";
        hl.textContent = msg.text;
        chatMessages.appendChild(hl);
      } else if (msg.type === "user-bubble") {
        const bubble = document.createElement("div");
        bubble.className = "msg-user-bubble";
        bubble.textContent = msg.text;
        chatMessages.appendChild(bubble);
      } else if (msg.type === "ai-card-error") {
        const card = document.createElement("div");
        card.className = "msg-ai-card";
        card.innerHTML = `
          <div class="ai-card-meta">${msg.meta}</div>
          <div class="ai-card-body">${msg.text}</div>
        `;
        chatMessages.appendChild(card);
      } else if (msg.type === "ai-card-success" || msg.type === "ai-card-out-of-scope") {
        const card = document.createElement("div");
        card.className = "msg-ai-card";
        const isOut = msg.type === "ai-card-out-of-scope";

        card.innerHTML = `
          <div class="ai-card-meta">${msg.meta}</div>
          <div class="ai-card-body">${msg.text.replace(/\n/g, "<br>")}</div>
          <div class="ai-feedback-section">
            <span class="feedback-label">Phản hồi này có hữu ích không?</span>
            <div class="feedback-buttons">
              <button class="fb-btn" title="Có">👍</button>
              <button class="fb-btn" title="Không">👎</button>
            </div>
            <div class="ai-status-row">
              <div class="confidence-bar-group">
                <div class="mini-bar-track">
                  <div class="mini-bar-fill" style="width: ${msg.confidence}%; background-color: ${
          msg.confidence > 80 ? "#10b981" : msg.confidence > 50 ? "#f59e0b" : "#ef4444"
        };"></div>
                </div>
                <span>${msg.confidence}% · ${msg.confidenceText}</span>
              </div>
              <span class="${isOut ? "status-badge-green" : "status-badge-green"}">● ${
          msg.statusText
        }</span>
            </div>
          </div>
        `;
        chatMessages.appendChild(card);
      }
    });

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // ==========================================================================
  // FLOW SWITCHER & EVENT HANDLERS
  // ==========================================================================

  flowBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      flowBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeFlow = btn.dataset.flow;

      // Update page if needed
      if (activeFlow === "highlight" || activeFlow === "ai-error") {
        switchPage(17);
      } else {
        switchPage(2);
      }

      renderMessages(mockFlows[activeFlow]);
    });
  });

  // Load default screenshot flow
  renderMessages(mockFlows.screenshot);

  // Send Message Logic
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = userMessageInput.value.trim();
    if (!text) return;

    // Add user message
    const currentMessages = mockFlows[activeFlow] || [];
    currentMessages.push({ type: "user-bubble", text: text });

    // Generate dynamic reply
    const lower = text.toLowerCase();
    if (lower.includes("logistics") || lower.includes("deadline") || lower.includes("tải file")) {
      currentMessages.push({
        type: "ai-card-out-of-scope",
        meta: "Ngoài phạm vi tài liệu học tập",
        text: "Hệ thống xác nhận câu hỏi chứa intent vận hành. Không tìm thấy thông tin này trong Slide Day 4. Bạn muốn tạo yêu cầu hỗ trợ tới TA không?",
        confidence: 25,
        confidenceText: "Thấp",
        statusText: "CẦN HỖ TRỢ TA"
      });
    } else {
      currentMessages.push({
        type: "ai-card-success",
        meta: `Ngữ cảnh: Slide trang ${currentPage}`,
        text: `Cảm ơn bạn đã hỏi "${text}". Dựa trên ngữ cảnh Slide trang ${currentPage}, câu trả lời được trích xuất trực tiếp từ bài giảng với độ căn cứ cao.`,
        confidence: 88,
        confidenceText: "Cao",
        statusText: "ĐÃ TRẢ LỜI"
      });
    }

    userMessageInput.value = "";
    renderMessages(currentMessages);

    // Update quota
    if (currentQuota < maxQuota) {
      currentQuota++;
      quotaCount.textContent = `${currentQuota}/${maxQuota} câu`;
      quotaFill.style.width = `${(currentQuota / maxQuota) * 100}%`;
    }
  });

  // Page Switcher Logic
  function switchPage(pageNum) {
    if (pageNum < 1) pageNum = 1;
    if (pageNum > totalPages) pageNum = totalPages;
    currentPage = pageNum;
    currentPageInput.value = currentPage;
    contextPillTag.textContent = `Trang slide: ${currentPage}`;

    // Highlight visible slide wrapper
    document.querySelectorAll(".slide-page-wrapper").forEach((wrap) => {
      wrap.classList.remove("active");
    });

    const activeWrap = document.getElementById(`pageWrapper${currentPage}`);
    if (activeWrap) {
      activeWrap.classList.add("active");
      activeWrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  prevPageBtn.addEventListener("click", () => switchPage(currentPage - 1));
  nextPageBtn.addEventListener("click", () => switchPage(currentPage + 1));

  currentPageInput.addEventListener("change", (e) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val)) switchPage(val);
  });

  // Highlight Text Interaction on Slide 17
  const markConstraints = document.getElementById("markConstraints");
  if (markConstraints) {
    markConstraints.addEventListener("click", () => {
      userMessageInput.value = "Giải thích đoạn bôi đen Constraints ở Trang 17";
      contextPillTag.textContent = "Bôi đen: “Constraints:”";
      userMessageInput.focus();
    });
  }

  // Sidebar Accordions
  const accordionHeaders = document.querySelectorAll(".accordion-header");
  accordionHeaders.forEach((header) => {
    header.addEventListener("click", () => {
      const item = header.parentElement;
      const isOpen = item.classList.contains("open");
      
      // Close others
      document.querySelectorAll(".accordion-item").forEach((acc) => {
        acc.classList.remove("open");
        const content = acc.querySelector(".accordion-content");
        if (content) content.classList.add("hidden");
        const chev = acc.querySelector(".chevron");
        if (chev) chev.classList.remove("rot-180");
      });

      if (!isOpen) {
        item.classList.add("open");
        const content = item.querySelector(".accordion-content");
        if (content) content.classList.remove("hidden");
        const chev = item.querySelector(".chevron");
        if (chev) chev.classList.add("rot-180");
      }
    });
  });

  // Document File Item Click
  const docItems = document.querySelectorAll(".doc-file-item");
  docItems.forEach((doc) => {
    doc.addEventListener("click", (e) => {
      e.stopPropagation();
      docItems.forEach((d) => d.classList.remove("active"));
      doc.classList.add("active");

      const filename = doc.dataset.doc;
      if (filename && currentDocFilename) {
        currentDocFilename.textContent = filename;
      }
    });
  });

  // Theme Toggle (Dark / Light)
  themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme");
  });

  // New Chat Clear
  newChatBtn.addEventListener("click", () => {
    mockFlows[activeFlow] = [];
    renderMessages([]);
  });
});
