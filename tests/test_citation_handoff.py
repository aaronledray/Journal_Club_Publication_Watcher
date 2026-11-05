import csv
import json

from output_modules.citation_handoff import export_selected_citations


def test_export_selected_citation_whitelists_fields_and_relation_metadata(tmp_path):
    source = tmp_path / "synthetic-results.json"
    output = tmp_path / "selected-citations.csv"
    source.write_text(
        json.dumps({
            "config_file_dict": {"email": "PRIVATE_CONFIG_SENTINEL", "topics": ["private search phrase"]},
            "keyword_frequency_dict": {"private search phrase": 1},
            "components": [
                {
                    "DOI": "10.1000/preprint",
                    "PMID": "111",
                    "Title": "Synthetic preprint title",
                    "Authors": ["Example Author", "Second Author"],
                    "Date": "2026-01-02",
                    "Journal": "bioRxiv",
                    "Source": "bioRxiv preprint search",
                    "IsPreprint": True,
                    "Link": "https://doi.org/10.1000/preprint",
                    "PublishedDOIs": ["10.1000/published"],
                    "RelatedDOIs": {"is-preprint-of": ["10.1000/published"]},
                    "MatchedKeywords": ["private search phrase"],
                    "Abstract": "Synthetic abstract that should not be exported",
                },
                {
                    "DOI": "10.1000/published",
                    "PMID": "222",
                    "Title": "Synthetic published title",
                    "Authors": ["Example Author"],
                    "Date": "2026-02-03",
                    "Journal": "Example Journal",
                    "IsPreprint": False,
                },
            ],
        }),
        encoding="utf-8",
    )

    export_selected_citations(
        str(source),
        ["DOI:https://doi.org/10.1000/PREPRINT"],
        str(output),
    )

    with output.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    row = rows[0]
    assert row["Record Type"] == "preprint"
    assert row["Relation DOI(s)"] == "10.1000/published"
    assert row["Relation PMID(s)"] == "222"
    assert row["Relation Title(s)"] == "Synthetic published title"
    assert row["Relation Source URL"] == "https://api.crossref.org/works/10.1000%2Fpreprint"
    exported_text = output.read_text(encoding="utf-8")
    assert "PRIVATE_CONFIG_SENTINEL" not in exported_text
    assert "private search phrase" not in exported_text
    assert "Synthetic abstract" not in exported_text


def test_export_requires_explicit_unambiguous_selection_and_does_not_overwrite(tmp_path):
    source = tmp_path / "results.json"
    source.write_text(
        json.dumps({"components": [
            {"Title": "Same title", "Date": "2025"},
            {"Title": "Same title", "Date": "2025"},
        ]}),
        encoding="utf-8",
    )
    output = tmp_path / "selected.csv"

    try:
        export_selected_citations(str(source), ["TITLE:Same title"], str(output))
    except ValueError as error:
        assert "multiple results" in str(error)
    else:
        raise AssertionError("Ambiguous exact-title selection should fail")

    output.write_text("preserve me", encoding="utf-8")
    try:
        export_selected_citations(str(source), ["TITLE:Same title"], str(output))
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing output should not be overwritten")
    assert output.read_text(encoding="utf-8") == "preserve me"
