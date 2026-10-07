"""Offline fixture coverage for CrossRef DOI relation handling."""

import json
import unittest
from copy import deepcopy
from pathlib import Path

from core.paper_processor import (
    extract_crossref_paper_info,
    extract_crossref_published_dois,
    extract_crossref_related_dois,
    process_crossref_papers,
    process_pubmed_papers,
    remove_duplicate_papers,
)
from fetch_modules.crossref_client import remove_duplicate_dois
from notify_modules.seen_tracker import get_component_ids
from notify_modules.email_sender import (
    _group_by_journal,
    build_html_body,
    build_plaintext_body,
)


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    with (FIXTURES / name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


class PublicationProcessingFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preprint = load_fixture("crossref_preprint_with_relations.json")
        cls.published = load_fixture(
            "crossref_published_with_reciprocal_preprint.json"
        )
        cls.standalone = load_fixture("crossref_work_without_relations.json")
        cls.pubmed_keyword_hit = load_fixture("pubmed_keyword_hit.json")

    def test_normalizes_and_deduplicates_multiple_related_dois(self):
        self.assertEqual(
            extract_crossref_related_dois(self.preprint),
            {
                "is-preprint-of": [
                    "10.1038/s41586-024-00001-2",
                    "10.1000/second",
                ],
                "has-preprint": ["10.1101/2024.01.01.0001"],
                "is-version-of": ["10.5555/related-work"],
            },
        )

    def test_only_preprint_to_publication_relations_are_published_dois(self):
        self.assertEqual(
            extract_crossref_published_dois(self.preprint),
            ["10.1038/s41586-024-00001-2", "10.1000/second"],
        )
        # The reciprocal relation identifies a preprint from the article side;
        # it remains available for identity matching, not as a published DOI.
        self.assertEqual(extract_crossref_published_dois(self.published), [])

    def test_component_preserves_relation_metadata_and_identity_aliases(self):
        component = extract_crossref_paper_info(self.preprint)

        self.assertEqual(component["DOI"], "10.1101/2024.01.01.0001")
        self.assertEqual(
            component["PublishedDOIs"],
            ["10.1038/s41586-024-00001-2", "10.1000/second"],
        )
        self.assertEqual(
            set(get_component_ids(component)),
            {
                "doi:10.1101/2024.01.01.0001",
                "doi:10.1038/s41586-024-00001-2",
                "doi:10.1000/second",
                "doi:10.5555/related-work",
            },
        )

    def test_missing_or_malformed_relations_produce_no_related_dois(self):
        self.assertEqual(extract_crossref_related_dois(self.standalone), {})
        self.assertEqual(extract_crossref_published_dois(self.standalone), [])
        self.assertEqual(extract_crossref_related_dois({"relation": None}), {})
        self.assertEqual(extract_crossref_related_dois({"relation": []}), {})

    def test_crossref_doi_deduplication_retains_each_matched_keyword(self):
        rows = [
            {"DOI": "10.1000/example", "search_keyword": "Alpha"},
            {"DOI": "10.1000/EXAMPLE", "search_keyword": "Beta"},
            {"DOI": "10.1000/example", "search_keyword": "alpha"},
        ]

        deduplicated = remove_duplicate_dois(rows)

        self.assertEqual(len(deduplicated), 1)
        self.assertEqual(deduplicated[0]["SearchKeywords"], ["Alpha", "Beta"])

    def test_pubmed_title_deduplication_retains_each_matched_keyword(self):
        alpha_hit = deepcopy(self.pubmed_keyword_hit)
        alpha_hit["search_keyword"] = "Alpha"
        beta_hit = deepcopy(self.pubmed_keyword_hit)
        beta_hit["search_keyword"] = "Beta"

        components = remove_duplicate_papers(
            process_pubmed_papers([alpha_hit, beta_hit])
        )

        self.assertEqual(len(components), 1)
        self.assertEqual(components[0]["MatchedKeywords"], ["Alpha", "Beta"])

    def test_crossref_doi_deduplication_flows_into_paper_components(self):
        rows = [
            {
                "DOI": "10.1000/relevance-example",
                "title": ["A paper found by two terms"],
                "search_keyword": "Alpha",
            },
            {
                "DOI": "10.1000/relevance-example",
                "title": ["A paper found by two terms"],
                "search_keyword": "Beta",
            },
        ]

        components = process_crossref_papers(remove_duplicate_dois(rows))

        self.assertEqual(components[0]["MatchedKeywords"], ["Alpha", "Beta"])

    def test_email_groups_rank_by_match_count_then_date(self):
        papers = [
            {
                "Title": "Single-term, newer",
                "Journal": "Journal A",
                "Date": "2025/06/01",
                "MatchedKeywords": ["Alpha"],
            },
            {
                "Title": "Multi-term, older",
                "Journal": "Journal A",
                "Date": "2025/01/01",
                "MatchedKeywords": ["Alpha", "Beta"],
            },
            {
                "Title": "Multi-term, newer",
                "Journal": "Journal A",
                "Date": "2025/05/01",
                "MatchedKeywords": ["Alpha", "Beta"],
            },
            {
                "Title": "Journal B paper",
                "Journal": "Journal B",
                "Date": "2025/04/01",
                "MatchedKeywords": ["Alpha"],
            },
        ]

        groups = _group_by_journal(papers)

        self.assertEqual([journal for journal, _ in groups], ["Journal A", "Journal B"])
        self.assertEqual(
            [paper["Title"] for paper in groups[0][1]],
            ["Multi-term, newer", "Multi-term, older", "Single-term, newer"],
        )
        body = build_plaintext_body(papers[:1], ("2025/01/01", "2025/06/30"))
        self.assertIn("Matched search terms: Alpha", body)
        html_body = build_html_body(papers[:1], ("2025/01/01", "2025/06/30"))
        self.assertIn("Matched search terms: Alpha", html_body)


if __name__ == "__main__":
    unittest.main()
