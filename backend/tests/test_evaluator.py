from __future__ import annotations

import json
import unittest
from pathlib import Path

from companion.retriever import load_corpus
from scripts.eval_golden_set import citations_match, evaluate_content


ROOT = Path(__file__).resolve().parents[1]


class EvaluatorScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = load_corpus()

    def test_single_keyword_and_citation_do_not_pass_claim_rubric(self) -> None:
        expected = {
            "claims": [
                {
                    "id": "ai_umbrella",
                    "signals_any": ["chiếc ô lớn nhất"],
                    "sources_any": ["Trang 3"],
                },
                {
                    "id": "ml_data",
                    "signals_any": ["học từ dữ liệu"],
                    "sources_any": ["Trang 3"],
                },
            ],
            "min_claims": 2,
        }

        content_pass, grounding_pass, details, failures = evaluate_content(
            "AI [Trang 3]",
            expected,
            self.corpus,
        )

        self.assertFalse(content_pass)
        self.assertFalse(grounding_pass)
        self.assertEqual([], details["matched_claims"])
        self.assertTrue(failures)

    def test_claim_with_wrong_page_fails_claim_level_grounding(self) -> None:
        expected = {
            "claims": [
                {
                    "id": "transformer",
                    "signals_any": ["Transformer", "attention"],
                    "sources_any": ["Trang 8"],
                }
            ],
            "min_claims": 1,
        }

        content_pass, grounding_pass, details, _ = evaluate_content(
            "Transformer dùng attention để nhìn các token quan trọng [Trang 3].",
            expected,
            self.corpus,
        )

        self.assertFalse(content_pass)
        self.assertFalse(grounding_pass)
        self.assertEqual(["transformer"], details["matched_claims"])
        self.assertEqual([], details["grounded_claims"])

    def test_claim_with_expected_page_passes(self) -> None:
        expected = {
            "claims": [
                {
                    "id": "transformer",
                    "signals_any": ["Transformer", "attention"],
                    "sources_any": ["Trang 8"],
                }
            ],
            "min_claims": 1,
        }

        content_pass, grounding_pass, details, failures = evaluate_content(
            "Transformer dùng attention để nhìn các token quan trọng [Trang 8].",
            expected,
            self.corpus,
        )

        self.assertTrue(content_pass)
        self.assertTrue(grounding_pass)
        self.assertEqual(["transformer"], details["grounded_claims"])
        self.assertEqual([], failures)

    def test_citation_only_suffix_is_attached_to_preceding_claim(self) -> None:
        expected = {
            "claims": [
                {
                    "id": "ml_data",
                    "signals_any": ["học từ dữ liệu"],
                    "sources_any": ["Trang 3"],
                }
            ],
            "min_claims": 1,
        }

        content_pass, grounding_pass, details, _ = evaluate_content(
            "Machine Learning học từ dữ liệu thay vì viết luật tay. [Trang 3]",
            expected,
            self.corpus,
        )

        self.assertTrue(content_pass)
        self.assertTrue(grounding_pass)
        self.assertEqual(["ml_data"], details["grounded_claims"])

    def test_numbered_output_is_scored_by_structure_not_literal_labels(self) -> None:
        expected = {
            "min_numbered_items": 3,
            "claims": [
                {
                    "id": "ai",
                    "signals_any": ["AI"],
                    "sources_any": ["Trang 3"],
                }
            ],
            "min_claims": 1,
        }
        answer = (
            "1. AI là chiếc ô lớn nhất. [Trang 3]\n"
            "2. Machine Learning học từ dữ liệu. [Trang 3]\n"
            "3. LLM là model ngôn ngữ nền. [Trang 3]"
        )

        content_pass, grounding_pass, details, failures = evaluate_content(
            answer,
            expected,
            self.corpus,
        )

        self.assertTrue(content_pass)
        self.assertTrue(grounding_pass)
        self.assertEqual([1, 2, 3], details["numbered_items"])
        self.assertEqual([], failures)

    def test_source_membership_still_rejects_unretrieved_citation(self) -> None:
        passed, failures = citations_match(
            ["Trang 8"],
            ["Trang 3"],
            {"behavior": "answer", "min_citations": 1},
        )

        self.assertFalse(passed)
        self.assertIn("citations were not retrieved", failures[0])


class GoldenSetVersionTests(unittest.TestCase):
    def test_v2_is_archived_and_v3_has_required_risk_coverage(self) -> None:
        v2 = json.loads((ROOT / "eval" / "golden_set_v2.json").read_text(encoding="utf-8"))
        v3 = json.loads((ROOT / "eval" / "golden_set_v3.json").read_text(encoding="utf-8"))

        self.assertEqual("2.0", v2["version"])
        self.assertEqual("3.0", v3["version"])
        self.assertGreaterEqual(len(v3["cases"]), 20)

        categories = [case["category"] for case in v3["cases"]]
        self.assertGreaterEqual(categories.count("Missing Evidence"), 2)
        self.assertGreaterEqual(categories.count("Ambiguous Scope"), 2)
        self.assertGreaterEqual(categories.count("Prohibited Assessment"), 2)
        self.assertGreaterEqual(categories.count("High Consequence Logistics"), 2)

        critical_cases = [case for case in v3["cases"] if case.get("critical")]
        observed_cases = [
            case
            for case in v3["cases"]
            if case.get("origin", "").startswith(("chatlog", "field_observation", "product_pain"))
        ]
        self.assertGreaterEqual(len(critical_cases), 8)
        self.assertGreaterEqual(len(observed_cases), 10)


if __name__ == "__main__":
    unittest.main()
