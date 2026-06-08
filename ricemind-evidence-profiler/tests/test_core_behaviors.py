from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_evidence_network import build_edges
from build_gene_report import add_mechanism_synthesis, data_driven_topic_groups, main as build_gene_report_main
from build_report_figures import build_figures_from_data_dir, update_markdown
from build_trait_report import main as build_trait_report_main
from normalize_ricemind_payload import extract_gene_mentions
from ricemind_api_client import RiceMindClient


class FakeClient(RiceMindClient):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, endpoint, **params):
        self.calls += 1
        index = min(self.calls - 1, len(self.responses) - 1)
        return self.responses[index]


class EvidenceNetworkTests(unittest.TestCase):
    def test_cross_sentence_pairs_are_not_direct_edges(self):
        sentences = [
            {"PMID": "1", "sent_id": "s1", "text": "OsA1 affects the first phenotype.", "gene": "OsA1", "trait": "trait one"},
            {"PMID": "1", "sent_id": "s2", "text": "OsB2 affects the second phenotype.", "gene": "OsB2", "trait": "trait two"},
        ]

        _, edges = build_edges(sentences)
        direct = {
            (edge["source"], edge["target"])
            for edge in edges
            if edge["edge_type"] == "gene-trait-sentence"
        }
        weak = {
            (edge["source"], edge["target"])
            for edge in edges
            if edge["edge_type"] == "gene-trait-pmid-cooccurrence"
        }

        self.assertEqual(direct, {("OsA1", "trait one"), ("OsB2", "trait two")})
        self.assertEqual(weak, {("OsA1", "trait two"), ("OsB2", "trait one")})


class GeneExtractionTests(unittest.TestCase):
    def test_free_text_excludes_generic_biology_abbreviations(self):
        mentions = extract_gene_mentions(
            {"gene": "", "text": "EXP IDA MAPK NADPH H2O OsNRT1.1B and DEP1 were discussed."}
        )

        self.assertEqual(mentions, ["DEP1", "OsNRT1.1B"])

    def test_explicit_gene_field_is_preserved(self):
        self.assertEqual(extract_gene_mentions({"gene": "Wx", "text": ""}), ["Wx"])


class PaginationTests(unittest.TestCase):
    def test_empty_first_page_stops_immediately(self):
        client = FakeClient([{"results": []}])

        payload = client.fetch_all("search-by-trait", result_keys=["results"], limit=100)

        self.assertEqual(client.calls, 1)
        self.assertTrue(payload["pagination_complete"])
        self.assertEqual(payload["pagination_stop_reason"], "empty_page")

    def test_repeated_full_page_stops_without_duplicate_records(self):
        page = {"results": [{"id": 1}]}
        client = FakeClient([page, page])

        payload = client.fetch_all("search-by-trait", result_keys=["results"], limit=1)

        self.assertEqual(client.calls, 2)
        self.assertEqual(payload["records"], [{"id": 1}])
        self.assertFalse(payload["pagination_complete"])
        self.assertEqual(payload["pagination_stop_reason"], "repeated_page")

    def test_max_pages_caps_an_endpoint_without_termination_metadata(self):
        client = FakeClient([
            {"results": [{"id": 1}]},
            {"results": [{"id": 2}]},
        ])

        payload = client.fetch_all("search-by-trait", result_keys=["results"], limit=1, max_pages=2)

        self.assertEqual(client.calls, 2)
        self.assertEqual(payload["records"], [{"id": 1}, {"id": 2}])
        self.assertFalse(payload["pagination_complete"])
        self.assertEqual(payload["pagination_stop_reason"], "max_pages")

    def test_full_vocabulary_requires_explicit_override(self):
        client = FakeClient([{"results": []}])

        with self.assertRaises(ValueError):
            client.fetch_all("all-genes", result_keys=["results"])


class MechanismWorkflowTests(unittest.TestCase):
    def test_sentence_evidence_requires_personalized_mechanism_markdown(self):
        with self.assertRaises(RuntimeError):
            add_mechanism_synthesis(
                None,
                "OsA1",
                [],
                [{"pmid": "1", "sentence": "OsA1 regulates a biological process."}],
                False,
            )

    def test_topic_groups_are_derived_from_sentence_text_not_trait(self):
        evidence = [
            {
                "trait": "trait one",
                "pmid": "1",
                "sentence": "Transporter expression in roots increases nitrogen uptake.",
                "title": "Root nitrogen transport",
            },
            {
                "trait": "trait two",
                "pmid": "2",
                "sentence": "Root transporter expression supports nitrogen uptake.",
                "title": "Nitrogen uptake regulation",
            },
        ]

        groups = data_driven_topic_groups(evidence, gene="OsA1")

        self.assertEqual(len(groups), 1)
        self.assertNotIn(groups[0][0], {"trait one", "trait two"})
        self.assertEqual(len(groups[0][1]), 2)

    def test_first_stage_writes_evidence_and_brief_without_docx(self):
        payload = {
            "gene_sentences": {
                "records": [
                    {
                        "PMID": "1",
                        "sent_id": "s1",
                        "text": "OsA1 regulates root development.",
                        "trait": "root development",
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "payload.json"
            out_path = root / "report.docx"
            input_json.write_text(json.dumps(payload), encoding="utf-8")
            argv = [
                "build_gene_report.py",
                "--gene",
                "OsA1",
                "--input-json",
                str(input_json),
                "--no-api",
                "--out",
                str(out_path),
            ]

            with patch.object(sys, "argv", argv):
                result = build_gene_report_main()

            data_dir = root / "report_data"
            self.assertEqual(result, 3)
            self.assertFalse(out_path.exists())
            self.assertTrue((data_dir / "report_normalized_evidence.csv").is_file())
            self.assertTrue((data_dir / "report_mechanism_synthesis_brief.md").is_file())


class ReportFigureTests(unittest.TestCase):
    @staticmethod
    def write_rows(path: Path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_breeding_sidecars_restore_legacy_figure_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "report_data"
            self.write_rows(
                data_dir / "report_candidate_ranking.csv",
                [
                    {
                        "target": "GeneA",
                        "tier1_direct_salt_article_support": "20",
                        "tier1_direct_salt_trait_count": "3",
                        "tier1_ion_homeostasis_trait_count": "4",
                        "tier1_yield_or_growth_trait_count": "2",
                        "salt_sentence_unique_pmids": "8",
                    },
                    {
                        "target": "GeneB",
                        "tier1_direct_salt_article_support": "10",
                        "tier1_direct_salt_trait_count": "2",
                        "tier1_ion_homeostasis_trait_count": "1",
                        "tier1_yield_or_growth_trait_count": "5",
                        "salt_sentence_unique_pmids": "4",
                    },
                ],
            )
            self.write_rows(
                data_dir / "report_sentence_evidence.csv",
                [
                    {"target": "GeneA", "PMID": "1", "year": "2020", "journal": "Journal A", "sentence": "Evidence."},
                    {"target": "GeneB", "PMID": "2", "year": "2021", "journal": "Journal B", "sentence": "Evidence."},
                ],
            )
            self.write_rows(
                data_dir / "report_tier1_traits.csv",
                [
                    {"target": "GeneA", "trait": "salt tolerance"},
                    {"target": "GeneB", "trait": "grain yield"},
                ],
            )

            figures = build_figures_from_data_dir(data_dir)
            names = {Path(item["path"]).name for item in figures}

            self.assertIn("candidate_evidence_support.png", names)
            self.assertIn("candidate_context_pmids.png", names)
            self.assertIn("objective_vs_yield_growth_trait_counts.png", names)
            self.assertIn("publication_year_distribution.png", names)
            self.assertIn("journal_distribution.png", names)
            self.assertIn("tier1_trait_distribution.png", names)
            self.assertTrue(all(Path(item["path"]).stat().st_size > 0 for item in figures))

    def test_markdown_figure_section_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "report.md"
            figure = root / "report_data" / "figures" / "example.png"
            figure.parent.mkdir(parents=True)
            figure.write_bytes(b"png")
            report.write_text("# Report\n", encoding="utf-8")
            figures = [{"path": str(figure), "caption": "Example evidence figure."}]

            update_markdown(report, figures)
            update_markdown(report, figures)
            text = report.read_text(encoding="utf-8")

            self.assertEqual(text.count("<!-- RICEMIND_FIGURES_START -->"), 1)
            self.assertEqual(text.count("![Example evidence figure.]"), 1)
            self.assertIn("report_data/figures/example.png", text)

    def test_trait_builder_generates_and_links_supported_figures(self):
        payload = {
            "results": [
                {
                    "PMID": "1",
                    "sent_id": "s1",
                    "text": "OsA1 regulates salt tolerance.",
                    "gene": "OsA1",
                    "trait": "salt tolerance",
                    "year": "2020",
                    "journal": "Journal A",
                },
                {
                    "PMID": "2",
                    "sent_id": "s2",
                    "text": "OsA1 supports ion homeostasis.",
                    "gene": "OsA1",
                    "trait": "ion homeostasis",
                    "year": "2021",
                    "journal": "Journal B",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_json = root / "payload.json"
            out_prefix = root / "salt"
            input_json.write_text(json.dumps(payload), encoding="utf-8")
            argv = [
                "build_trait_report.py",
                "--trait",
                "salt tolerance",
                "--out-prefix",
                str(out_prefix),
                "--input-json",
                str(input_json),
            ]

            with patch.object(sys, "argv", argv):
                build_trait_report_main()

            report = root / "salt_trait_evidence_summary.md"
            fig_dir = root / "salt_trait_evidence_summary_data" / "figures"
            text = report.read_text(encoding="utf-8")
            self.assertIn("## Evidence Figures", text)
            self.assertTrue((fig_dir / "publication_year_distribution.png").is_file())
            self.assertTrue((fig_dir / "top_candidate_genes_by_sentence_count.png").is_file())
            self.assertTrue((fig_dir / "top_candidate_genes_by_unique_pmids.png").is_file())
            self.assertTrue((fig_dir / "journal_distribution.png").is_file())


if __name__ == "__main__":
    unittest.main()
