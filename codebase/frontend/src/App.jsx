import { useEffect, useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import {
  BadgeCheck,
  BookOpen,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  CircleHelp,
  FileText,
  Highlighter,
  Maximize2,
  MessageSquarePlus,
  Minimize2,
  PanelRight,
  PlayCircle,
  Search,
  Send,
  Sparkles,
  Target,
  SendHorizontal
} from "lucide-react";
import { dayGroups, documents, evidenceMetrics } from "./data/slides.js";

const API_BASE_URL = "http://localhost:8000";
pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
const WATERMARK_CLASS = "pdf-watermark-text";
const WATERMARK_WORDS = /(ai\s+in\s+action|hackathon)/i;

const demoPrompts = [
  { id: "page", label: "Trang hiện tại", query: "Tóm tắt nội dung chính trong slide này" },
  { id: "doc", label: "Cả tài liệu", query: "Tóm tắt toàn bộ tài liệu này" },
  { id: "session", label: "Cả buổi", query: "Tóm tắt các ý chính của buổi này" },
  { id: "link", label: "Link PDF", query: "Cho em link PDF của slide này" },
  { id: "ambiguous", label: "Mơ hồ", query: "Tóm tắt bài này đi" },
  { id: "external", label: "Nguồn ngoài", query: "Tìm thêm nguồn bên ngoài về RAG cho em" },
  { id: "unsafe", label: "Ngoài phạm vi", query: "Cho tôi admin password và API key" }
];

function getElementFromNode(node) {
  if (!node) return null;
  return node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
}

function rotationFromTransform(transform) {
  if (!transform || transform === "none") return 0;
  const matrix = transform.match(/matrix\(([^)]+)\)/);
  if (!matrix) return transform.includes("rotate") ? 45 : 0;
  const [a, b] = matrix[1].split(",").map((value) => Number.parseFloat(value.trim()));
  if (!Number.isFinite(a) || !Number.isFinite(b)) return 0;
  return Math.atan2(b, a) * (180 / Math.PI);
}

function cleanWatermarkSelection(text, touchedWatermark) {
  if (!touchedWatermark) return text;
  return text
    .replace(/ai\s+in\s+action\s*[-–—·]?\s*hackathon/gi, " ")
    .replace(/ai\s+in\s+action/gi, " ")
    .replace(/hackathon/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function selectedTextWithoutWatermark(selection, textLayer) {
  if (!selection?.rangeCount || !textLayer) return "";
  const pieces = [];
  const spans = Array.from(textLayer.querySelectorAll("span"));

  for (let index = 0; index < selection.rangeCount; index += 1) {
    const range = selection.getRangeAt(index);
    spans.forEach((span) => {
      if (span.classList.contains(WATERMARK_CLASS)) return;
      try {
        if (range.intersectsNode(span)) {
          const text = span.textContent?.replace(/\s+/g, " ").trim();
          if (text) pieces.push(text);
        }
      } catch {
        // Ignore spans that cannot be compared with the selection range.
      }
    });
  }

  return [...new Set(pieces)].join(" ").replace(/\s+/g, " ").trim();
}

function VLogo() {
  return (
    <svg
      width="34"
      height="34"
      viewBox="0 0 34 34"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="v-logo-svg"
      aria-hidden="true"
    >
      <filter id="logo-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="1.5" floodColor="#0b4285" floodOpacity="0.25" />
      </filter>
      <g filter="url(#logo-shadow)">
        <path d="M 6 5 L 15 5 L 9 11 Z" fill="#d01616" />
        <path d="M 9 11 L 15 5 L 17 16 L 22 5 L 30 5 L 17 27 Z" fill="#0b4285" />
      </g>
    </svg>
  );
}

function App() {
  const [docId, setDocId] = useState(documents[0].id);
  const [expandedDays, setExpandedDays] = useState({ day01: true, day02: false });
  const [page, setPage] = useState(2);
  const [selectedText, setSelectedText] = useState("");
  const [selectionMenu, setSelectionMenu] = useState(null);
  const [selectionNotes, setSelectionNotes] = useState([]);
  const [pdfPageCount, setPdfPageCount] = useState(documents[0].pageCount);
  const [pdfPageWidth, setPdfPageWidth] = useState(0);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [draftTicket, setDraftTicket] = useState(null);
  const [isSubmittingTicket, setIsSubmittingTicket] = useState(false);
  const [isChatCollapsed, setIsChatCollapsed] = useState(false);
  const wheelNavRef = useRef(0);
  const pdfFrameRef = useRef(null);
  const chatLogRef = useRef(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      mode: "live",
      status: "🟢 Fast API Connected",
      confidence: 95,
      scope: { label: "Trang hiện tại", reason: "Kết nối FastAPI Backend & NVIDIA Provider." },
      sources: [],
      text: "Xin chào. Hệ thống đã kết nối trực tiếp với **FastAPI Backend Pipeline (NVIDIA Model & Telegram TA Bot)**. Bạn có thể hỏi theo trang, cả tài liệu, hay cả buổi học."
    }
  ]);

  const doc = useMemo(() => documents.find((item) => item.id === docId) || documents[0], [docId]);
  const slide = useMemo(() => doc.slides.find((item) => item.page === page) || doc.slides[0], [doc, page]);
  const pageCount = pdfPageCount || doc.pageCount;
  const currentSelectionNotes = useMemo(
    () => selectionNotes.filter((note) => note.docId === doc.id && note.page === slide.page),
    [selectionNotes, doc.id, slide.page]
  );
  const progress = Math.round((messages.filter((item) => item.role === "user").length / 15) * 100);

  useEffect(() => {
    if (isChatCollapsed) return undefined;
    const frameId = requestAnimationFrame(() => {
      const chatLog = chatLogRef.current;
      if (!chatLog) return;
      chatLog.scrollTo({
        top: chatLog.scrollHeight,
        behavior: messages.length > 1 ? "smooth" : "auto"
      });
    });
    return () => cancelAnimationFrame(frameId);
  }, [messages, isLoading, isChatCollapsed]);

  useEffect(() => {
    function closeSelectionMenu(event) {
      if (event.target.closest(".selection-menu") || event.target.closest(".pdf-frame")) return;
      setSelectionMenu(null);
    }

    function closeOnEscape(event) {
      if (event.key === "Escape") setSelectionMenu(null);
    }

    document.addEventListener("mousedown", closeSelectionMenu);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeSelectionMenu);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  useEffect(() => {
    let frameId = 0;

    function updatePageWidth() {
      cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(() => {
        const frame = pdfFrameRef.current;
        if (!frame) return;
        const nextWidth = Math.max(320, Math.min(960, Math.floor(frame.getBoundingClientRect().width)));
        setPdfPageWidth((currentWidth) => {
          if (!currentWidth) return nextWidth;
          return Math.abs(currentWidth - nextWidth) > 8 ? nextWidth : currentWidth;
        });
      });
    }

    updatePageWidth();
    window.addEventListener("resize", updatePageWidth);
    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", updatePageWidth);
    };
  }, []);

  function changeDoc(nextDoc, initialPage = 1) {
    setDocId(nextDoc.id);
    setPage(initialPage);
    setPdfPageCount(nextDoc.pageCount);
    setSelectedText("");
    setSelectionMenu(null);
    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        mode: "system",
        status: "Đổi tài liệu",
        confidence: 86,
        scope: { label: "Tài liệu hiện tại", reason: `Đã mở ${nextDoc.filename}.` },
        sources: [],
        text: `Đã chuyển sang ${nextDoc.title} (Trang ${initialPage}).`
      }
    ]);
  }

  async function ask(rawQuery, forcedScopeStr = null) {
    const cleanQuery = rawQuery.trim();
    if (!cleanQuery || isLoading) return;

    setIsChatCollapsed(false);
    setQuestion("");
    setIsLoading(true);

    setMessages((current) => [...current, { role: "user", text: cleanQuery }]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/companion/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: cleanQuery,
          current_day: doc.dayId || "day01",
          current_page: page,
          selection: selectedText,
          forced_scope: forcedScopeStr
        })
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage = {
        role: "assistant",
        mode: ["live", "external"].includes(data.mode) ? "live" : "rule",
        status: data.mode === "external" ? "🌐 WEB GROUNDED" : data.mode === "live" ? "🟢 LIVE API" : "🟡 RULE",
        confidence: data.confidence === "cao" ? 95 : 75,
        model: data.model,
        scope: {
          scope: data.scope,
          label: data.scope_label,
          reason: data.needs_clarification ? "Cần người học xác nhận phạm vi." : `Phạm vi ${data.scope_label}`
        },
        sources: Array.isArray(data.citations) ? data.citations : [],
        text: data.answer,
        needs_clarification: data.needs_clarification,
        clarification_options: data.clarification_options,
        ta_handoff_suggested: data.ta_handoff_suggested
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      console.warn("Backend API call failed:", error);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          mode: "guardrail",
          status: "Backend chưa sẵn sàng",
          confidence: 0,
          scope: {
            scope: "unavailable",
            label: "Chưa có kết quả",
            reason: "Không nhận được response đã xác minh từ backend."
          },
          sources: [],
          text:
            "Mình chưa nhận được câu trả lời đã xác minh từ backend nên không hiển thị nội dung hoặc citation tạm. Bạn có thể thử lại hoặc chuyển câu hỏi cho TA.",
          ta_handoff_suggested: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  }


  function clampSelectionMenuPosition(clientX, clientY) {
    const menuWidth = 320;
    const menuHeight = 150;
    return {
      x: Math.max(12, Math.min(clientX, window.innerWidth - menuWidth - 12)),
      y: Math.max(12, Math.min(clientY + 12, window.innerHeight - menuHeight - 12))
    };
  }

  function handleSelectionPointerDown(event) {
    if (event.button !== 0) return;
    setSelectionMenu(null);
  }

  function handleSelectionPointerUp(event) {
    const selection = window.getSelection?.();
    const selected = selection?.toString().replace(/\s+/g, " ").trim();
    const textLayer = event.currentTarget.querySelector(".react-pdf__Page__textContent");
    const selectionRange = selection?.rangeCount ? selection.getRangeAt(0) : null;
    const selectionStartsInPdf =
      selection?.anchorNode && textLayer?.contains(getElementFromNode(selection.anchorNode));
    const selectionEndsInPdf =
      selection?.focusNode && textLayer?.contains(getElementFromNode(selection.focusNode));
    const touchedWatermark =
      selectionRange &&
      Array.from(textLayer?.querySelectorAll(`.${WATERMARK_CLASS}`) || []).some((node) => {
        try {
          return selectionRange.intersectsNode(node);
        } catch {
          return false;
        }
      });
    const cleanedSelection = touchedWatermark
      ? cleanWatermarkSelection(selectedTextWithoutWatermark(selection, textLayer), true)
      : selected;

    if (!cleanedSelection || !selectionStartsInPdf || !selectionEndsInPdf) {
      selection?.removeAllRanges();
      setSelectedText("");
      setSelectionMenu(null);
      return;
    }

    setSelectedText(cleanedSelection);
    setSelectionMenu(clampSelectionMenuPosition(event.clientX, event.clientY));
  }

  function markWatermarkTextLayer() {
    requestAnimationFrame(() => {
      const textLayer = pdfFrameRef.current?.querySelector(".react-pdf__Page__textContent");
      if (!textLayer) return;

      textLayer.querySelectorAll("span").forEach((span) => {
        const normalizedText = span.textContent?.replace(/\s+/g, " ").trim() || "";
        const rect = span.getBoundingClientRect();
        const rotation = Math.abs(rotationFromTransform(window.getComputedStyle(span).transform));
        const isHackathon = /hackathon/i.test(normalizedText);
        const isLargeAiInAction = /ai\s+in\s+action/i.test(normalizedText) && rect.width > 170;
        const isDiagonal = rotation > 8 && rotation < 82;

        if (isDiagonal || isHackathon || isLargeAiInAction || (WATERMARK_WORDS.test(normalizedText) && rect.width > 220)) {
          span.classList.add(WATERMARK_CLASS);
          span.setAttribute("aria-hidden", "true");
        }
      });
    });
  }

  function goToPage(nextPage) {
    const safePage = Math.max(1, Math.min(nextPage, pageCount));
    setPage(safePage);
    setSelectedText("");
    setSelectionMenu(null);
  }

  function handleNavigateCitation(sourceStr) {
    const pageMatch = sourceStr.match(/Trang\s+(\d+)/i);
    const pageNum = pageMatch ? Number(pageMatch[1]) : null;

    const matchedDoc = documents.find(
      (d) => sourceStr.toLowerCase().includes(d.filename.toLowerCase()) || sourceStr.toLowerCase().includes(d.id.toLowerCase())
    );

    const targetDoc = matchedDoc || doc;
    const targetPage = pageNum || 1;

    if (targetDoc.id !== doc.id) {
      changeDoc(targetDoc, targetPage);
    } else {
      goToPage(targetPage);
    }

    if (pdfFrameRef.current) {
      pdfFrameRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function handleSlideWheel(event) {
    if (Math.abs(event.deltaY) < 18) return;
    event.preventDefault();

    const now = Date.now();
    if (now - wheelNavRef.current < 420) return;
    wheelNavRef.current = now;

    goToPage(page + (event.deltaY > 0 ? 1 : -1));
  }

  function openDraftTicket(userQuery, reason = "Hỗ trợ học viên") {
    setDraftTicket({
      student_query: userQuery || "Yêu cầu hỗ trợ từ học viên",
      reason: reason,
      current_day: doc?.dayId || "day01",
      current_page: page,
      note: ""
    });
  }

  async function submitDraftTicket() {
    if (!draftTicket) return;
    setIsSubmittingTicket(true);
    try {
      const resp = await fetch(`${API_BASE_URL}/api/v1/escalate-ta`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: `${draftTicket.reason}${draftTicket.note ? ` | Note: ${draftTicket.note}` : ""}`,
          student_query: draftTicket.student_query,
          current_day: draftTicket.current_day,
          current_page: draftTicket.current_page
        })
      });
      if (!resp.ok) throw new Error(`TA handoff failed: ${resp.status}`);
      const data = await resp.json();
      alert(data.message);
      setDraftTicket(null);
    } catch (e) {
      alert("Chưa thể gửi yêu cầu cho TA. Vui lòng kiểm tra kết nối và thử lại.");
    } finally {
      setIsSubmittingTicket(false);
    }
  }

  async function escalateToTA(userQuery) {
    openDraftTicket(userQuery);
  }
  function askAboutSelection() {
    if (!selectedText.trim()) return;
    ask(`Giải thích đoạn bôi đen này: ${selectedText}`, "selected_text");
    setSelectionMenu(null);
  }

  function reportConfusion() {
    if (!selectedText.trim()) return;
    setMessages((current) => [
      ...current,
      { role: "user", text: `Em đang bối rối ở đoạn: ${selectedText}` },
      {
        role: "assistant",
        mode: "confusion-report",
        status: "Đã ghi nhận",
        confidence: 92,
        scope: {
          scope: "selected_text",
          label: "Đoạn bôi đen",
          reason: "Bối rối được gắn trực tiếp với đoạn đã chọn trên slide."
        },
        sources: [],
        text:
          "Mình đã ghi nhận điểm bối rối cho đoạn này. Trong bản demo, trạng thái này có thể dùng để đẩy tín hiệu cho TA hoặc ưu tiên giải thích lại theo đúng slide."
      }
    ]);
    setSelectionMenu(null);
  }

  function addSelectionNote() {
    if (!selectedText.trim()) return;
    setSelectionNotes((current) => [
      ...current,
      {
        id: `${doc.id}-${slide.page}-${Date.now()}`,
        docId: doc.id,
        page: slide.page,
        text: selectedText
      }
    ]);
    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        mode: "note",
        status: "Đã ghi chú",
        confidence: 100,
        scope: {
          scope: "selected_text",
          label: "Đoạn bôi đen",
          reason: "Ghi chú được lưu mock ở frontend theo trang hiện tại."
        },
        sources: [],
        text: `Đã lưu ghi chú cho đoạn bôi đen ở trang ${slide.page}.`
      }
    ]);
    setSelectionMenu(null);
  }

  function toggleDay(dayId) {
    setExpandedDays((prev) => ({ ...prev, [dayId]: !prev[dayId] }));
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-cluster">
          <button className="icon-button" type="button" aria-label="Quay lại">
            <ChevronLeft size={18} />
          </button>
          <div className="brand-logo">
            <VLogo />
            <strong className="brand-name">
              <span className="v-red">V</span>
              <span className="learn-blue">Learn</span>
            </strong>
          </div>
        </div>

      </header>

      <main className={`workspace ${isChatCollapsed ? "workspace--chat-collapsed" : ""}`}>
        <aside className="library-panel">
          <div className="sidebar-header">
            <div className="header-icon-box">
              <BookOpen size={18} />
            </div>
            <div className="header-text">
              <h3>Học liệu môn học</h3>
              <p>Chương, slide và tài liệu đã upload</p>
            </div>
          </div>

          <div className="sidebar-divider" />

          <div className="day-accordion-list">
            {dayGroups.map((group) => {
              const isExpanded = Boolean(expandedDays[group.dayId]);
              return (
                <div key={group.dayId} className={`accordion-card ${isExpanded ? "expanded" : ""}`}>
                  <button
                    type="button"
                    className="accordion-header"
                    onClick={() => toggleDay(group.dayId)}
                  >
                    <div className="accordion-left">
                      <PlayCircle size={18} className="play-icon" />
                      <div className="accordion-title-group">
                        <strong>{group.dayLabel}</strong>
                        <span>{group.subtitle}</span>
                      </div>
                    </div>
                    <div className="accordion-right">
                      {group.status ? <span className="status-badge">{group.status}</span> : null}
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="accordion-content">
                      {group.docs.map((item) => {
                        const isSelected = item.id === doc.id;
                        return (
                          <button
                            key={item.id}
                            type="button"
                            className={`doc-card ${isSelected ? "active" : ""}`}
                            onClick={() => changeDoc(item)}
                          >
                            <div className="doc-card-left">
                              <PlayCircle size={16} className="doc-play-icon" />
                              <div className="doc-card-info">
                                <strong>{item.filename}</strong>
                                <span>{item.pageCount} trang</span>
                              </div>
                            </div>
                            {isSelected && <CheckCircle2 size={16} className="check-icon" />}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>


        </aside>

        <section className="viewer-panel">
          <div className="viewer-toolbar">
            <div>
              <button className="tool-button active" type="button">
                <BookOpen size={16} />
                Đọc
              </button>
            </div>
            <div className="scope-chip">
              <PanelRight size={16} />
              Trang {page} / {pageCount}
            </div>
          </div>

          <div className="slide-stage">
            <div
              className="pdf-frame"
              ref={pdfFrameRef}
              onMouseDown={handleSelectionPointerDown}
              onMouseUp={handleSelectionPointerUp}
              onWheel={handleSlideWheel}
            >
              <Document
                key={doc.id}
                file={doc.pdfUrl}
                className="pdf-document"
                loading={<div className="pdf-load-state">Đang tải PDF...</div>}
                error={<div className="pdf-load-state error">Không mở được PDF từ data/slides.</div>}
                onLoadSuccess={({ numPages }) => {
                  setPdfPageCount((currentCount) => (currentCount === numPages ? currentCount : numPages));
                }}
              >
                <Page
                  key={`${doc.id}-${page}`}
                  className="pdf-page"
                  pageNumber={page}
                  width={pdfPageWidth || 900}
                  renderAnnotationLayer
                  renderTextLayer
                  onRenderTextLayerSuccess={markWatermarkTextLayer}
                  loading={<div className="pdf-load-state">Đang render trang...</div>}
                />
              </Document>
            </div>
          </div>

          <div className="page-nav">
            <button
              className="icon-button"
              type="button"
              disabled={page <= 1}
              onClick={() => {
                goToPage(page - 1);
              }}
            >
              <ChevronLeft size={18} />
            </button>
            <input
              aria-label="Số trang"
              value={page}
              onChange={(event) => {
                const next = Number(event.target.value);
                if (Number.isInteger(next) && next >= 1 && next <= pageCount) {
                  goToPage(next);
                }
              }}
            />
            <button
              className="icon-button"
              type="button"
              disabled={page >= pageCount}
              onClick={() => {
                goToPage(page + 1);
              }}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </section>

        <aside className="tutor-panel">
          <div className="tutor-header">
            <div className="tutor-title">
              <div className="bot-avatar">
                <Bot size={20} />
              </div>
              <div>
                <h2>VLearn Tutor</h2>
              </div>
            </div>
            <div style={{ display: "flex", gap: "4px" }}>
              <button className="icon-button" type="button" onClick={() => setIsChatCollapsed(true)} aria-label="Thu gọn Chatbot" title="Thu gọn VLearn Tutor (Toàn màn hình Slide)">
                <Minimize2 size={18} />
              </button>
              <button className="icon-button" type="button" onClick={() => setMessages([])} aria-label="Tạo hội thoại mới" title="Xóa hội thoại">
                <MessageSquarePlus size={18} />
              </button>
            </div>
          </div>


          <div className="scenario-row">
            {demoPrompts.map((prompt) => (
              <button key={prompt.id} type="button" onClick={() => ask(prompt.query)}>
                {prompt.label}
              </button>
            ))}
          </div>

          <div className="chat-log" ref={chatLogRef}>
            {messages.length === 0 ? (
              <div className="empty-state">
                <Sparkles size={22} />
                <p>Chọn một scenario hoặc nhập câu hỏi để bắt đầu.</p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div className={`message ${message.role}`} key={`${message.role}-${index}`}>
                  {message.role === "user" ? (
                    <p>{message.text}</p>
                  ) : (
                    <>
                      <div className="message-meta">
                        <span>{message.scope?.label}</span>
                      </div>
                      <div className="message-markdown">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkBreaks]}
                          components={{
                            a: ({ node: _node, ...props }) => (
                              <a {...props} target="_blank" rel="noopener noreferrer" />
                            )
                          }}
                        >
                          {message.text}
                        </ReactMarkdown>
                      </div>
                      {message.sources?.length > 0 ? (() => {
                        const renderedSources = message.sources.map((source, sourceIndex) => {
                          const citation = typeof source === "string"
                            ? { label: source, kind: "unknown", title: source, source_id: source }
                            : source;
                          const key = `${citation.kind}-${citation.source_id}-${citation.label}-${sourceIndex}`;
                          const tooltip = citation.excerpt
                            ? `${citation.title}: ${citation.excerpt}`
                            : citation.title;

                          if (citation.url) {
                            return (
                              <a
                                key={key}
                                href={citation.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="source-chip source-chip--page"
                                title={tooltip}
                              >
                                🌐 {citation.title} [{citation.label}] ↗
                              </a>
                            );
                          }

                          if (citation.kind === "slide" || citation.kind === "selection") {
                            const navigationTarget = `${citation.source_id} - ${citation.label}`;
                            return (
                              <button
                                key={key}
                                type="button"
                                className="source-chip source-chip--page"
                                onClick={() => handleNavigateCitation(navigationTarget)}
                                title={tooltip}
                              >
                                📄 {citation.title} · {citation.label}
                              </button>
                            );
                          }

                          if (citation.kind === "transcript") {
                            const dayDoc = documents.find((item) => item.dayId === citation.day);
                            return (
                              <button
                                key={key}
                                type="button"
                                className="source-chip source-chip--page"
                                onClick={() => dayDoc && handleNavigateCitation(`${dayDoc.filename} - Trang 1`)}
                                disabled={!dayDoc}
                                title={tooltip}
                              >
                                🎙 {citation.title} [{citation.label}]
                              </button>
                            );
                          }

                          return null;
                        }).filter(Boolean);

                        if (renderedSources.length === 0) return null;

                        return (
                          <div className="source-section">
                            <span className="section-label">Trích dẫn (Grounding Sources):</span>
                            <div className="source-list">{renderedSources}</div>
                          </div>
                        );
                      })() : null}
                      {message.needs_clarification ? (
                        <div className="clarify-actions">
                          <button type="button" onClick={() => ask("Tóm tắt trang này", "current_page")}>Trang hiện tại</button>
                          <button type="button" onClick={() => ask("Tóm tắt cả tài liệu này", "current_document")}>Cả tài liệu</button>
                          <button type="button" onClick={() => ask("Tóm tắt cả buổi học hôm nay", "whole_session")}>Cả buổi học</button>
                        </div>
                      ) : null}

                      <div className="ta-action-row" style={{ marginTop: "10px" }}>
                        <button
                          type="button"
                          className="ta-button"
                          style={{
                            background: "#e11d48",
                            color: "#fff",
                            border: "none",
                            padding: "6px 12px",
                            borderRadius: "6px",
                            fontSize: "12px",
                            fontWeight: "600",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "6px"
                          }}
                          onClick={() => escalateToTA(messages[index - 1]?.text || message.text)}
                        >
                          <SendHorizontal size={14} />
                          Chuyển TA (Telegram Push)
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}

          </div>

          <form
            className="ask-form"
            onSubmit={(event) => {
              event.preventDefault();
              ask(question);
            }}
          >
            <div className="input-shell">
              <Search size={16} />
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Nhập câu hỏi hoặc hỏi theo slide..."
              />
              <button type="submit" aria-label="Gửi câu hỏi" disabled={isLoading}>
                <Send size={16} />
              </button>
            </div>
          </form>


        </aside>
      </main>
      {selectionMenu && selectedText ? (
        <div
          className="selection-menu"
          style={{ left: `${selectionMenu.x}px`, top: `${selectionMenu.y}px` }}
          onMouseDown={(event) => event.stopPropagation()}
        >
          <div className="selection-summary">
            <Highlighter size={15} />
            <span>{selectedText}</span>
          </div>
          <div className="selection-actions">
            <button type="button" onClick={askAboutSelection}>
              <Bot size={14} />
              Hỏi AI
            </button>
            <button type="button" onClick={reportConfusion}>
              <CircleHelp size={14} />
              Báo bối rối
            </button>
            <button type="button" onClick={addSelectionNote}>
              <FileText size={14} />
              Ghi chú
            </button>
          </div>
          {currentSelectionNotes.length > 0 ? (
            <div className="selection-notes">
              {currentSelectionNotes.slice(-2).map((note) => (
                <span key={note.id}>Ghi chú: {note.text}</span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {draftTicket && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: "rgba(15, 23, 42, 0.75)", backdropFilter: "blur(4px)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
        }}>
          <div style={{
            background: "#1e293b", border: "1px solid #334155", borderRadius: "12px",
            padding: "24px", width: "90%", maxWidth: "480px", color: "#f8fafc",
            boxShadow: "0 20px 25px -5px rgba(0,0,0,0.5)"
          }}>
            <h3 style={{ margin: "0 0 16px 0", fontSize: "18px", color: "#38bdf8", display: "flex", alignItems: "center", gap: "8px" }}>
              📝 Draft Ticket Hỗ Trợ TA (Human-in-the-loop)
            </h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "14px" }}>
              <div>
                <label style={{ color: "#94a3b8", fontSize: "12px", fontWeight: "600" }}>CÂU HỎI CỦA HỌC VIÊN</label>
                <input
                  type="text"
                  value={draftTicket.student_query}
                  onChange={(e) => setDraftTicket({ ...draftTicket, student_query: e.target.value })}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#fff", marginTop: "4px" }}
                />
              </div>

              <div style={{ display: "flex", gap: "12px" }}>
                <div style={{ flex: 1 }}>
                  <label style={{ color: "#94a3b8", fontSize: "12px", fontWeight: "600" }}>BUỔI HỌC (DAY)</label>
                  <input
                    type="text"
                    value={draftTicket.current_day}
                    readOnly
                    style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#94a3b8", marginTop: "4px" }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ color: "#94a3b8", fontSize: "12px", fontWeight: "600" }}>TRANG SLIDE</label>
                  <input
                    type="text"
                    value={`Trang ${draftTicket.current_page}`}
                    readOnly
                    style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#94a3b8", marginTop: "4px" }}
                  />
                </div>
              </div>

              <div>
                <label style={{ color: "#94a3b8", fontSize: "12px", fontWeight: "600" }}>GHI CHÚ THÊM CHO TA (TÙY CHỌN)</label>
                <textarea
                  rows={3}
                  value={draftTicket.note}
                  onChange={(e) => setDraftTicket({ ...draftTicket, note: e.target.value })}
                  placeholder="Gõ thêm thông báo hoặc câu hỏi cụ thể cho TA..."
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#fff", marginTop: "4px", resize: "none" }}
                />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "20px" }}>
              <button
                onClick={() => setDraftTicket(null)}
                style={{ background: "#334155", color: "#cbd5e1", border: "none", padding: "8px 16px", borderRadius: "6px", fontWeight: "600", cursor: "pointer" }}
              >
                Hủy
              </button>
              <button
                onClick={submitDraftTicket}
                disabled={isSubmittingTicket}
                style={{ background: "#22c55e", color: "#fff", border: "none", padding: "8px 16px", borderRadius: "6px", fontWeight: "600", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px" }}
              >
                🚀 {isSubmittingTicket ? "Đang gửi..." : "Gửi cho TA"}
              </button>
            </div>
          </div>
        </div>
      )}

      {isChatCollapsed && (
        <button
          type="button"
          className="floating-chat-trigger"
          onClick={() => setIsChatCollapsed(false)}
          title="Mở VLearn Tutor"
        >
          <Bot size={22} />
          <span>Hỏi VLearn Tutor</span>
        </button>
      )}
    </div>
  );
}

export default App;
