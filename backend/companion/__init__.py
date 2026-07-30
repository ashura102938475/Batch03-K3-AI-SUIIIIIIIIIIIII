"""Lõi của VLearn Smart Contextual Companion.

Tách khỏi UI để eval (CP3) gọi lại được cùng logic mà không cần Streamlit:

    scope.detect_intent / detect_scope  -> quyết định trung tâm, rule-based
    retriever.search                    -> lấy chunk theo đúng phạm vi
    answer.generate                     -> sinh câu trả lời có căn cứ (Gemini thật)
    trace.write_turn_trace              -> log/trace làm evidence
"""
