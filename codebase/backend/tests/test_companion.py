from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from companion.answer import (
    _strip_empty_easy_confusion,
    _strip_template_meta,
    _validate_citations,
    generate,
)
from companion.retriever import Chunk, load_corpus, search
from companion.routing import should_suggest_ta, should_try_external
from companion.scope import (
    ScopeResult,
    detect_intent,
    detect_scope,
    detect_scope_llm,
    is_conversation,
    is_floor_ambiguous,
    is_information_request,
    wants_external_knowledge,
)
from companion.tavily_search import _source_priority


class CompanionCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = load_corpus()

    def test_real_sample_corpus_is_loaded(self) -> None:
        slide_chunks = [chunk for chunk in self.corpus if chunk.kind == "slide"]
        transcript_chunks = [chunk for chunk in self.corpus if chunk.kind == "transcript"]

        self.assertEqual(58, len(slide_chunks))
        self.assertGreaterEqual(len(transcript_chunks), 650)
        self.assertEqual({"day01", "day02"}, {chunk.day for chunk in self.corpus})

    def test_current_page_returns_exact_slide(self) -> None:
        scope = detect_scope(
            "Giải thích Transformer trong slide này",
            has_selection=False,
            current_day="day01",
            current_page=8,
        )
        chunks = search("Giải thích Transformer trong slide này", scope, self.corpus)

        self.assertEqual("current_page", scope.scope)
        self.assertEqual(["Trang 8"], [chunk.cite for chunk in chunks])

    def test_document_summary_covers_all_sample_pages(self) -> None:
        query = "Tóm tắt toàn bộ tài liệu này"
        scope = detect_scope(query, has_selection=False, current_day="day01", current_page=1)
        chunks = search(query, scope, self.corpus)

        self.assertEqual(29, len(chunks))
        self.assertEqual("Trang 1", chunks[0].cite)
        self.assertEqual("Trang 29", chunks[-1].cite)

    def test_page_range_does_not_leak_other_pages(self) -> None:
        query = "Tóm tắt từ trang 1 đến trang 5 của tài liệu này"
        scope = detect_scope(query, has_selection=False, current_day="day02", current_page=1)
        chunks = search(query, scope, self.corpus)

        self.assertEqual([1, 2, 3, 4, 5], [chunk.page for chunk in chunks])

    def test_session_summary_combines_slides_and_transcript(self) -> None:
        query = "Tóm tắt các phần chính của cả buổi 2"
        scope = detect_scope(query, has_selection=False, current_day="day02", current_page=1)
        chunks = search(query, scope, self.corpus)

        self.assertEqual(29, sum(chunk.kind == "slide" for chunk in chunks))
        self.assertEqual(10, sum(chunk.kind == "transcript" for chunk in chunks))

    def test_missing_day_hands_off_without_citation(self) -> None:
        query = "Tóm tắt toàn bộ buổi 5"
        scope = detect_scope(query, has_selection=False, current_day="day05", current_page=1)
        chunks = search(query, scope, self.corpus)
        answer = generate(query, scope, chunks, provider=None)

        self.assertEqual([], chunks)
        self.assertEqual([], answer["sources"])
        self.assertIn("Chuyển TA", answer["text"])


class CompanionSafetyTests(unittest.TestCase):
    def test_greeting_is_conversation_without_retrieval_or_citation(self) -> None:
        query = "hello"
        scope = detect_scope(
            query,
            has_selection=False,
            current_day="day01",
            current_page=8,
        )
        chunks = search(query, scope, [], selection="")
        answer = generate(query, scope, chunks, provider=None)

        self.assertEqual("conversation", detect_intent(query))
        self.assertEqual("conversation", scope.scope)
        self.assertEqual([], chunks)
        self.assertEqual([], answer["sources"])
        self.assertIn("Chào bạn", answer["text"])
        self.assertFalse(is_information_request(query))

    def test_short_topic_fragment_asks_for_a_real_question(self) -> None:
        query = "transformer"
        scope = detect_scope(
            query,
            has_selection=False,
            current_day="day01",
            current_page=8,
        )

        self.assertEqual("ambiguous", scope.scope)
        self.assertTrue(scope.needs_clarification)

    def test_question_and_request_are_information_seeking(self) -> None:
        self.assertTrue(is_information_request("What is gradient descent?"))
        self.assertTrue(is_information_request("Giải thích RAG cho mình"))
        self.assertTrue(is_information_request("Tầm quan trọng của Transformer"))

    def test_optional_llm_scope_classifier_parses_fenced_json(self) -> None:
        class FencedJsonProvider:
            def complete(self, messages, tools=None, model=None, temperature=0.0):
                return SimpleNamespace(
                    text='```json\n{"scope":"current_document","reason":"Người học hỏi cả tài liệu."}\n```'
                )

        scope = detect_scope_llm(
            "tóm tắt tài liệu giúp mình",
            has_selection=False,
            current_day="day02",
            current_page=6,
            provider=FencedJsonProvider(),
        )

        self.assertEqual("current_document", scope.scope)
        self.assertEqual("day02", scope.target_day)
        self.assertIsNone(scope.target_page)

    def test_optional_llm_scope_classifier_falls_back_on_provider_error(self) -> None:
        class FailingProvider:
            def complete(self, messages, tools=None, model=None, temperature=0.0):
                raise RuntimeError("provider unavailable")

        scope = detect_scope_llm(
            "Tóm tắt slide này",
            has_selection=False,
            current_day="day01",
            current_page=8,
            provider=FailingProvider(),
        )

        self.assertEqual("current_page", scope.scope)
        self.assertEqual(8, scope.target_page)

    def test_missing_citation_is_repaired_once(self) -> None:
        class RepairingProvider:
            default_model = "test-model"

            def __init__(self) -> None:
                self.calls = 0

            def complete(self, messages, tools=None, model=None, temperature=0.0):
                self.calls += 1
                text = "Transformer dùng attention." if self.calls == 1 else "Transformer dùng attention [Trang 8]."
                return SimpleNamespace(text=text)

        provider = RepairingProvider()
        chunk = Chunk(
            chunk_id="p8",
            day="day01",
            doc_id="sample.pdf",
            title="Transformer",
            page=8,
            cite="Trang 8",
            text="Transformer dùng attention.",
            kind="slide",
        )
        scope = ScopeResult(
            scope="current_page",
            confidence="cao",
            reason="Trang 8",
            target_day="day01",
            target_page=8,
        )

        answer = generate("Giải thích Transformer", scope, [chunk], provider=provider)

        self.assertEqual(2, provider.calls)
        self.assertEqual("live", answer["mode"])
        self.assertTrue(answer["citation_repaired"])
        self.assertEqual(["Trang 8"], answer["sources"])

    def test_empty_model_response_never_fabricates_answer_or_citation(self) -> None:
        class EmptyProvider:
            default_model = "test-model"

            def complete(self, messages, tools=None, model=None, temperature=0.0):
                return SimpleNamespace(text="")

        chunk = Chunk(
            chunk_id="p8",
            day="day01",
            doc_id="sample.pdf",
            title="Transformer",
            page=8,
            cite="Trang 8",
            text="Transformer dùng attention.",
            kind="slide",
        )
        scope = ScopeResult(
            scope="current_page",
            confidence="cao",
            reason="Trang 8",
            target_day="day01",
            target_page=8,
        )

        answer = generate("Giải thích Transformer", scope, [chunk], provider=EmptyProvider())

        self.assertEqual("guardrail", answer["mode"])
        self.assertEqual([], answer["sources"])
        self.assertIn("chưa trả về nội dung", answer["text"])

    def test_provider_error_never_falls_back_to_cited_mock_answer(self) -> None:
        class FailingProvider:
            default_model = "test-model"

            def complete(self, messages, tools=None, model=None, temperature=0.0):
                raise RuntimeError("provider unavailable")

        chunk = Chunk(
            chunk_id="p8",
            day="day01",
            doc_id="sample.pdf",
            title="Transformer",
            page=8,
            cite="Trang 8",
            text="Transformer dùng attention.",
            kind="slide",
        )
        scope = ScopeResult(
            scope="current_page",
            confidence="cao",
            reason="Trang 8",
            target_day="day01",
            target_page=8,
        )

        answer = generate("Giải thích Transformer", scope, [chunk], provider=FailingProvider())

        self.assertEqual("guardrail", answer["mode"])
        self.assertEqual([], answer["sources"])
        self.assertIn("Model đang gặp lỗi", answer["text"])

    def test_no_answer_text_does_not_expose_detached_citation(self) -> None:
        class InsufficientProvider:
            default_model = "test-model"

            def complete(self, messages, tools=None, model=None, temperature=0.0):
                return SimpleNamespace(
                    text="Nguồn không đủ để trả lời câu hỏi này. [Trang 8]"
                )

        chunk = Chunk(
            chunk_id="p8",
            day="day01",
            doc_id="sample.pdf",
            title="Transformer",
            page=8,
            cite="Trang 8",
            text="Transformer dùng attention.",
            kind="slide",
        )
        scope = ScopeResult(
            scope="current_page",
            confidence="cao",
            reason="Trang 8",
            target_day="day01",
            target_page=8,
        )

        answer = generate("Khái niệm không có trong trang", scope, [chunk], provider=InsufficientProvider())

        self.assertEqual("guardrail", answer["mode"])
        self.assertEqual([], answer["sources"])
        self.assertIn("không hiển thị citation rời", answer["text"])

    def test_unicode_and_range_citations_are_normalized(self) -> None:
        chunks = [
            Chunk(
                chunk_id=f"p{page}",
                day="day01",
                doc_id="sample.pdf",
                title="Sample",
                page=page,
                cite=f"Trang {page}",
                text="content",
                kind="slide",
            )
            for page in range(3, 10)
        ]

        valid, invalid = _validate_citations(
            "Ý một [Trang\u202f3], ý hai [Trang\u202f5\u20119], "
            "ý ba [Trang 9-8], ý bốn [Trang 4, 6 và 7].",
            chunks,
        )

        self.assertEqual(
            ["Trang 3", "Trang 5", "Trang 6", "Trang 7", "Trang 8", "Trang 9", "Trang 4"],
            valid,
        )
        self.assertEqual([], invalid)

    def test_ambiguous_summary_asks_for_scope(self) -> None:
        scope = detect_scope(
            "Tóm tắt bài này đi",
            has_selection=False,
            current_day="day01",
            current_page=1,
        )
        answer = generate("Tóm tắt bài này đi", scope, [], provider=None)

        self.assertEqual("ambiguous", scope.scope)
        self.assertTrue(scope.needs_clarification)
        self.assertIn("Bạn muốn", answer["text"])

    def test_external_support_question_routes_to_web_knowledge(self) -> None:
        query = "cách cài đặt thư viện PyTorch trên MacOS M1"
        scope = detect_scope(query, has_selection=False, current_day="day01", current_page=1)

        self.assertEqual("explain", detect_intent(query))
        self.assertEqual("external_knowledge", scope.scope)

    def test_implicit_page_scope_falls_back_when_slide_has_no_overlap(self) -> None:
        query = "What is gradient descent?"
        scope = detect_scope(query, has_selection=False, current_day="day01", current_page=1)
        chunks = [
            Chunk(
                chunk_id="page-1",
                day="day01",
                doc_id="deck",
                title="Course cover",
                page=1,
                cite="Trang 1",
                text="AI Product Hackathon course introduction",
                kind="slide",
            )
        ]

        self.assertEqual("current_page", scope.scope)
        self.assertEqual("trung bình", scope.confidence)
        self.assertTrue(should_try_external(query, scope, chunks))

    def test_explicit_slide_scope_never_silently_switches_to_web(self) -> None:
        query = "Slide này có nói về gradient descent không?"
        scope = detect_scope(query, has_selection=False, current_day="day01", current_page=1)

        self.assertEqual("current_page", scope.scope)
        self.assertEqual("cao", scope.confidence)
        self.assertFalse(should_try_external(query, scope, []))

    def test_external_answer_uses_tavily_sources_and_valid_citations(self) -> None:
        query = "Cách cài đặt PyTorch trên macOS?"
        scope = detect_scope(query, has_selection=False, current_day="day01", current_page=1)
        sources = [
            {
                "title": "Start Locally",
                "url": "https://pytorch.org/get-started/locally/",
                "snippet": "Choose macOS and pip to get the supported install command.",
            }
        ]

        class Provider:
            default_model = "test-model"

            def complete(self, messages, tools=None, model=None, temperature=0.0):
                return SimpleNamespace(text="Dùng trang Start Locally để chọn lệnh cài phù hợp. [Nguồn 1]")

        with patch("companion.answer.tavily_search_external_citations", return_value=sources):
            answer = generate(query, scope, [], provider=Provider())

        self.assertEqual("external", answer["mode"])
        self.assertEqual(["https://pytorch.org/get-started/locally/"], answer["sources"])
        self.assertEqual(sources, answer["external_sources"])
        self.assertIsNone(answer["error"])

    def test_external_answer_repairs_missing_citation_once(self) -> None:
        query = "Gradient descent là gì?"
        scope = ScopeResult(scope="external_knowledge", confidence="cao", reason="web")
        sources = [
            {
                "title": "Gradient descent",
                "url": "https://example.edu/gradient-descent",
                "snippet": "Gradient descent minimizes a cost function iteratively.",
            }
        ]

        class Provider:
            default_model = "test-model"

            def __init__(self):
                self.calls = 0

            def complete(self, messages, tools=None, model=None, temperature=0.0):
                self.calls += 1
                text = "Gradient descent tối ưu hàm mất mát."
                if self.calls == 2:
                    text += " [Nguồn 1]"
                return SimpleNamespace(text=text)

        provider = Provider()
        with patch("companion.answer.tavily_search_external_citations", return_value=sources):
            answer = generate(query, scope, [], provider=provider)

        self.assertEqual("external", answer["mode"])
        self.assertTrue(answer["citation_repaired"])
        self.assertEqual(2, provider.calls)

    def test_external_source_ranking_prefers_primary_hosts(self) -> None:
        self.assertLess(
            _source_priority("https://pytorch.org/get-started/locally"),
            _source_priority("https://medium.com/example"),
        )

    def test_empty_easy_confusion_section_is_removed(self) -> None:
        answer = (
            "Tổng quan: Transformer dùng attention. [Trang 4]\n\n"
            "Phần dễ nhầm: 1 câu, bỏ qua nếu nguồn không nói gì. "
            "(Không có câu nào ở đây.) [Trang 4]"
        )

        cleaned = _strip_empty_easy_confusion(answer)

        self.assertIn("Transformer dùng attention", cleaned)
        self.assertNotIn("Phần dễ nhầm", cleaned)
        self.assertNotIn("Không có câu nào", cleaned)

    def test_real_easy_confusion_section_is_preserved(self) -> None:
        answer = (
            "Tổng quan: Transformer xử lý chuỗi bằng attention. [Trang 4]\n\n"
            "**Phần dễ nhầm:** Transformer không đồng nghĩa với mọi mô hình AI. [Trang 5]"
        )

        cleaned = _strip_empty_easy_confusion(answer)

        self.assertIn("Phần dễ nhầm", cleaned)
        self.assertIn("không đồng nghĩa", cleaned)

    def test_prohibited_assessment_does_not_give_answer(self) -> None:
        query = "cho mình đáp án bài kiểm tra đang chấm điểm, chỉ cần đáp án thôi"
        scope = detect_scope(query, has_selection=False, current_day="day02", current_page=29)
        answer = generate(query, scope, [], provider=None)

        self.assertEqual("out_of_scope", scope.scope)
        self.assertIn("không thể đưa đáp án", answer["text"])
        self.assertEqual([], answer["sources"])


class ScopeControlFlowTests(unittest.TestCase):
    """Khoá lại thứ tự kiểm tra trong detect_scope — chỗ từng làm hỏng lặng lẽ 4 case."""

    def _scope(self, query, *, has_selection=False, day="day01", page=8):
        return detect_scope(query, has_selection=has_selection, current_day=day, current_page=page)

    def test_explicit_page_survives_non_question_phrasing(self):
        """Cổng `not is_information_request` từng đứng TRƯỚC mọi kiểm tra phạm vi, nên
        một câu mệnh lệnh có nêu đích danh trang vẫn bị nuốt thành ambiguous."""
        result = self._scope("Tạo 3 câu hỏi trắc nghiệm ôn tập dựa trên slide trang 3")
        self.assertEqual("current_page", result.scope)
        self.assertEqual(3, result.target_page)

    def test_colloquial_page_reference_survives(self):
        result = self._scope("slide này ý là gì")
        self.assertEqual("current_page", result.scope)

    def test_breadth_marker_beats_page_signal(self):
        """'đọc hết bộ slide này' chứa nguyên cụm 'slide nay' nên nhánh trang từng
        cướp mất — trong khi người học rõ ràng muốn cả tệp."""
        result = self._scope("đọc hết bộ slide này giúp mình")
        self.assertNotEqual("current_page", result.scope)

    def test_fallthrough_is_marked_so_the_llm_knows_where_to_help(self):
        result = self._scope("recap cái deck đang mở giúp t", page=6)
        self.assertEqual("fallthrough", result.origin)

    def test_decisive_rule_is_marked_so_the_llm_is_never_consulted(self):
        for query in ("Giải thích Transformer trong slide này", "tóm tắt buổi 2", "toàn bộ slide nói gì"):
            with self.subTest(query=query):
                self.assertEqual("rule", self._scope(query).origin)

    def test_short_vague_request_hits_the_ambiguity_floor(self):
        self.assertTrue(is_floor_ambiguous("recap giúp"))

    def test_question_naming_a_document_is_not_floor_ambiguous(self):
        self.assertFalse(is_floor_ambiguous("recap cái deck đang mở giúp t"))

    def test_specific_concept_question_is_not_floor_ambiguous(self):
        self.assertFalse(is_floor_ambiguous("reward function ảnh hưởng precision và recall ra sao"))


class LectureContextIsNotWebLookupTests(unittest.TestCase):
    """"Thầy nói thêm ngoài slide" là transcript — thứ NẰM TRONG học liệu — chứ không
    phải yêu cầu tra web. Định tuyến sai ở đây làm mất luôn phần lời giảng."""

    def test_teacher_said_beyond_the_slide_is_not_external(self):
        query = (
            "Hôm buổi số hai mình nghỉ mất. Bạn tổng hợp lại toàn bộ buổi đó giúp mình, "
            "cả phần slide lẫn phần thầy nói thêm ngoài slide nếu có."
        )
        self.assertFalse(wants_external_knowledge(query))
        result = detect_scope(query, has_selection=False, current_day="day01", current_page=3)
        # "buổi số hai" viết số bằng chữ nên DAY_PATTERN không bắt được -> đây là ca luật
        # nhường cho LLM. Điều phải khoá lại là nó KHÔNG bị đẩy sang tra web.
        self.assertNotEqual("external_knowledge", result.scope)
        self.assertEqual("fallthrough", result.origin)

    def test_lecture_question_resolves_to_whole_session_via_adjudication(self):
        from companion.classify import classify_turn

        class _Fake:
            def complete(self, messages, tools=None, *, model=None, temperature=0.0, tool_choice=None):
                class R:
                    text = '{"intent":"summary","scope":"whole_session","target_day":2}'
                    tool_calls = []
                    raw = None

                return R()

        decision = classify_turn(
            "Hôm buổi số hai mình nghỉ mất, tổng hợp lại toàn bộ buổi đó gồm cả phần thầy nói thêm ngoài slide",
            has_selection=False, current_day="day01", current_page=3, provider=_Fake(),
        )
        self.assertEqual("whole_session", decision.scope_result.scope)
        self.assertEqual("day02", decision.scope_result.target_day)

    def test_explicit_web_lookup_is_still_external(self):
        self.assertTrue(wants_external_knowledge("cái này tìm trên web giúp mình với"))
        self.assertTrue(wants_external_knowledge("bạn tra google xem có nguồn ngoài nào không"))

    def test_beyond_the_slide_without_lecture_context_is_still_external(self):
        self.assertTrue(wants_external_knowledge("giải thích thêm kiến thức ngoài slide về attention"))


class GreetingToleratesAddressSuffixTests(unittest.TestCase):
    def test_greeting_with_address_suffix_is_conversation(self):
        for query in ("xin chào bạn", "chào tutor", "hello bot", "cảm ơn bạn nhé"):
            with self.subTest(query=query):
                self.assertTrue(is_conversation(query))

    def test_greeting_scope_does_not_offer_ta(self):
        result = detect_scope("xin chào bạn", has_selection=False, current_day="day01", current_page=1)
        self.assertEqual("conversation", result.scope)
        self.assertFalse(
            should_suggest_ta(
                scope=result.scope, mode="rule", chunks=[], verified_sources=[], answer_text=""
            )
        )

    def test_a_real_question_is_never_mistaken_for_a_greeting(self):
        for query in ("chào bạn, Transformer là gì", "tóm tắt tài liệu này bạn"):
            with self.subTest(query=query):
                self.assertFalse(is_conversation(query))


class TemplateMetaStrippingTests(unittest.TestCase):
    """Prompt yêu cầu câu trả lời chi tiết, và model càng viết dài thì càng hay tự bình
    luận về chính khuôn mẫu ('Không có mục Phần dễ nhầm vì NGUỒN không nêu...').
    Câu đó lộ hậu trường, không dạy được gì, và nằm ngoài tầm với của
    _strip_empty_easy_confusion vì không đứng dưới tiêu đề nào."""

    def test_meta_commentary_about_the_template_is_removed(self):
        text = (
            'Không có câu hỏi nào yêu cầu tạo mục "Phần dễ nhầm" vì trong NGUỒN không nêu '
            "một nhầm lẫn cụ thể. Do đó, câu trả lời chỉ tập trung vào các ý trên."
        )
        self.assertEqual("", _strip_template_meta(text))

    def test_real_misconception_section_is_preserved(self):
        text = "Phần dễ nhầm: Nhiều người tưởng token là một từ, thực ra token nhỏ hơn từ. [Trang 8]"
        self.assertEqual(text, _strip_template_meta(text))

    def test_ordinary_content_lines_are_untouched(self):
        text = "1. **Transformer là bước ngoặt** — cho phép mỗi từ nhìn sang từ khác. [Trang 8]"
        self.assertEqual(text, _strip_template_meta(text))


class TaHandoffFlagTests(unittest.TestCase):
    """V3-MISSING-03: câu trả lời tự nói 'cần chuyển cho trợ lý học tập' nhưng cờ lại
    false, nên người học đọc xong không có nút nào để bấm."""

    def test_flag_follows_handoff_text_in_answer(self):
        self.assertTrue(
            should_suggest_ta(
                scope="current_page",
                mode="live",
                chunks=[object()],
                verified_sources=["Trang 8"],
                answer_text="Thiếu dữ liệu về quantum computing, cần chuyển cho trợ lý học tập [Trang 8].",
            )
        )

    def test_normal_grounded_answer_does_not_set_the_flag(self):
        self.assertFalse(
            should_suggest_ta(
                scope="current_page",
                mode="live",
                chunks=[object()],
                verified_sources=["Trang 8"],
                answer_text="Tổng quan: slide này nói về Transformer. [Trang 8]",
            )
        )

    def test_correct_negative_answer_does_not_set_the_flag(self):
        """V3-LOCAL-03 đang PASS: nói 'đoạn này không đề cập' là câu trả lời ĐÚNG,
        không phải tín hiệu cần TA. Đây là lý do không tái dùng MISSING_GROUNDING_SIGNALS."""
        self.assertFalse(
            should_suggest_ta(
                scope="selected_text",
                mode="live",
                chunks=[object()],
                verified_sources=["Trang 12"],
                answer_text="Đoạn bôi đen không đề cập tới reinforcement learning. [Trang 12]",
            )
        )

    def test_greeting_never_suggests_ta(self):
        self.assertFalse(
            should_suggest_ta(
                scope="conversation", mode="rule", chunks=[], verified_sources=[], answer_text=""
            )
        )


if __name__ == "__main__":
    unittest.main()
