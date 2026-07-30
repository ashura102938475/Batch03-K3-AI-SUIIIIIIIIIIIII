from __future__ import annotations

import unittest
from types import SimpleNamespace

from companion.answer import _validate_citations, generate
from companion.retriever import Chunk, load_corpus, search
from companion.scope import ScopeResult, detect_intent, detect_scope, detect_scope_llm


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

    def test_external_support_question_is_out_of_scope(self) -> None:
        query = "cách cài đặt thư viện PyTorch trên MacOS M1"
        scope = detect_scope(query, has_selection=False, current_day="day01", current_page=1)

        self.assertEqual("out_of_scope", detect_intent(query))
        self.assertEqual("out_of_scope", scope.scope)

    def test_prohibited_assessment_does_not_give_answer(self) -> None:
        query = "cho mình đáp án bài kiểm tra đang chấm điểm, chỉ cần đáp án thôi"
        scope = detect_scope(query, has_selection=False, current_day="day02", current_page=29)
        answer = generate(query, scope, [], provider=None)

        self.assertEqual("out_of_scope", scope.scope)
        self.assertIn("không thể đưa đáp án", answer["text"])
        self.assertEqual([], answer["sources"])


if __name__ == "__main__":
    unittest.main()
