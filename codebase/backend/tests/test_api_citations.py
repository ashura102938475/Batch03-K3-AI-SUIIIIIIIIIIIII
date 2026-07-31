from __future__ import annotations

import unittest

from api import build_citation_payloads, source_values
from companion.retriever import Chunk


class CitationPayloadTests(unittest.TestCase):
    def test_only_retrieved_sources_become_ui_citations(self) -> None:
        chunk = Chunk(
            chunk_id="page-8",
            day="day01",
            doc_id="d1-slide-hackathon.pdf",
            title="Transformer",
            page=8,
            cite="Trang 8",
            text="Transformer sử dụng attention để xử lý quan hệ giữa các token.",
            kind="slide",
        )
        answer = {
            "text": "Transformer sử dụng attention. [Trang 8]",
            "mode": "live",
            "sources": ["Trang 8", "Trang 99"],
            "external_sources": [],
        }

        citations = build_citation_payloads(answer, [chunk])

        self.assertEqual(["Trang 8"], source_values(citations))
        self.assertEqual("d1-slide-hackathon.pdf", citations[0].source_id)
        self.assertEqual(8, citations[0].page)
        self.assertIn("attention", citations[0].excerpt)

    def test_web_citation_requires_matching_tavily_result(self) -> None:
        url = "https://pytorch.org/get-started/locally/"
        answer = {
            "text": "Xem hướng dẫn cài đặt chính thức. [Nguồn 1]",
            "mode": "external",
            "sources": [url, "https://unverified.example/"],
            "external_sources": [
                {
                    "title": "Start Locally",
                    "url": url,
                    "snippet": "Choose the supported operating system and package manager.",
                }
            ],
        }

        citations = build_citation_payloads(answer, [])

        self.assertEqual([url], source_values(citations))
        self.assertEqual("web", citations[0].kind)
        self.assertEqual("Nguồn 1", citations[0].label)

    def test_no_answer_sources_produce_no_ui_citations(self) -> None:
        chunk = Chunk(
            chunk_id="page-8",
            day="day01",
            doc_id="d1-slide-hackathon.pdf",
            title="Transformer",
            page=8,
            cite="Trang 8",
            text="Transformer sử dụng attention.",
            kind="slide",
        )
        citations = build_citation_payloads(
            {
                "text": "",
                "mode": "live",
                "sources": ["Trang 8"],
                "external_sources": [],
            },
            [chunk],
        )

        self.assertEqual([], citations)
        self.assertEqual([], source_values(citations))


if __name__ == "__main__":
    unittest.main()
