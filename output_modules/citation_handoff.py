"""Export explicitly selected citations without copying search configuration.

This module deliberately does not import the configuration loader. It reads the
``components`` array from a Watcher results JSON file and writes a small,
allowlisted CSV suitable for local review in other research tools.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple
from urllib.parse import quote


CSV_FIELDS = (
    "DOI",
    "PMID",
    "Title",
    "Authors",
    "Publication Date",
    "Journal",
    "Record Type",
    "URL",
    "Relation DOI(s)",
    "Relation PMID(s)",
    "Relation Title(s)",
    "Relation Type(s)",
    "Relation Source URL",
)


def normalize_doi(value: Any) -> str:
    """Normalize a DOI value or DOI URL for exact matching."""
    doi = str(value or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.casefold().startswith(prefix):
            doi = doi[len(prefix):].strip()
            break
    return doi.rstrip(".,; ").casefold()


def _normalize_selection(selector: str) -> Tuple[str, str]:
    if ":" not in selector:
        raise ValueError("Selections must use DOI:<value>, PMID:<value>, or TITLE:<exact title>.")

    kind, value = selector.split(":", 1)
    kind = kind.strip().upper()
    value = value.strip()
    if not value or kind not in {"DOI", "PMID", "TITLE"}:
        raise ValueError("Selections must use DOI:<value>, PMID:<value>, or TITLE:<exact title>.")
    if kind == "DOI":
        value = normalize_doi(value)
    elif kind == "PMID":
        value = re.sub(r"^PMID\s*:\s*", "", value, flags=re.IGNORECASE).strip()
    else:
        value = " ".join(value.split()).casefold()
    return kind, value


def _component_matches(component: Dict[str, Any], kind: str, value: str) -> bool:
    if kind == "DOI":
        return normalize_doi(component.get("DOI")) == value
    if kind == "PMID":
        return str(component.get("PMID") or "").strip() == value
    title = " ".join(str(component.get("Title") or "").split()).casefold()
    return title == value


def _as_values(value: Any) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _relation_map(component: Dict[str, Any]) -> Dict[str, List[str]]:
    relations = component.get("RelatedDOIs") or {}
    if not isinstance(relations, dict):
        relations = {}
    cleaned: Dict[str, List[str]] = {}
    for relation_type, values in relations.items():
        dois = []
        for value in _as_values(values):
            doi = normalize_doi(value)
            if doi and doi not in dois:
                dois.append(doi)
        if dois:
            cleaned[str(relation_type)] = dois

    published_dois = [normalize_doi(value) for value in _as_values(component.get("PublishedDOIs"))]
    published_dois = [doi for doi in published_dois if doi]
    if published_dois:
        existing = cleaned.setdefault("is-preprint-of", [])
        for doi in published_dois:
            if doi not in existing:
                existing.append(doi)
    return cleaned


def _citation_row(component: Dict[str, Any], components: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    relation_map = _relation_map(component)
    related_dois = [doi for doi_list in relation_map.values() for doi in doi_list]
    related_dois = list(dict.fromkeys(related_dois))
    relation_types = list(relation_map)

    by_doi: Dict[str, List[Dict[str, Any]]] = {}
    for candidate in components:
        doi = normalize_doi(candidate.get("DOI"))
        if doi:
            by_doi.setdefault(doi, []).append(candidate)

    related_records = [
        by_doi[doi][0]
        for doi in related_dois
        if len(by_doi.get(doi, [])) == 1
    ]
    source_doi = normalize_doi(component.get("DOI"))
    relation_source = (
        "https://api.crossref.org/works/" + quote(source_doi, safe="")
        if source_doi and relation_map
        else ""
    )

    is_preprint = bool(component.get("IsPreprint"))
    source = str(component.get("Source") or "").casefold()
    if not is_preprint and "preprint" in source:
        is_preprint = True

    doi = normalize_doi(component.get("DOI"))
    url = str(component.get("Link") or "").strip()
    if doi:
        url = f"https://doi.org/{doi}"
    if url.casefold() in {"", "no link available", "n/a"}:
        url = ""

    authors = component.get("Authors") or []
    if not isinstance(authors, (list, tuple)):
        authors = [authors]

    return {
        "DOI": doi,
        "PMID": str(component.get("PMID") or "").strip(),
        "Title": str(component.get("Title") or "").strip(),
        "Authors": "; ".join(str(author).strip() for author in authors if str(author).strip()),
        "Publication Date": str(component.get("Date") or "").strip(),
        "Journal": str(component.get("Journal") or "").strip(),
        "Record Type": "preprint" if is_preprint else "published",
        "URL": url,
        "Relation DOI(s)": "; ".join(related_dois),
        "Relation PMID(s)": "; ".join(
            str(record.get("PMID") or "").strip()
            for record in related_records
            if str(record.get("PMID") or "").strip()
        ),
        "Relation Title(s)": "; ".join(
            str(record.get("Title") or "").strip()
            for record in related_records
            if str(record.get("Title") or "").strip()
        ),
        "Relation Type(s)": "; ".join(relation_types),
        "Relation Source URL": relation_source,
    }


def export_selected_citations(
    input_path: str,
    selections: Iterable[str],
    output_path: str,
) -> Path:
    """Write explicitly selected, allowlisted citation metadata to CSV.

    ``config_file_dict``, keyword frequencies, matched search terms, and all
    other fields from the results file are intentionally omitted.
    """
    source_path = Path(input_path)
    target_path = Path(output_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Results JSON not found: {source_path}")
    if target_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {target_path}")

    with source_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    components = data.get("components") if isinstance(data, dict) else None
    if not isinstance(components, list):
        raise ValueError("Results JSON must contain a components array.")

    parsed_selections = [_normalize_selection(value) for value in selections]
    if not parsed_selections:
        raise ValueError("Select at least one citation with --select.")

    selected_indices = set()
    for kind, value in parsed_selections:
        matches = [
            index
            for index, component in enumerate(components)
            if isinstance(component, dict) and _component_matches(component, kind, value)
        ]
        if not matches:
            raise ValueError(f"No result matched {kind}:{value}.")
        if len(matches) > 1:
            raise ValueError(f"{kind}:{value} matched multiple results; select by a unique DOI or PMID.")
        selected_indices.add(matches[0])

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for index in sorted(selected_indices):
            component = components[index]
            writer.writerow(_citation_row(component, components))
    return target_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export only explicitly selected citation metadata from a Watcher results JSON. "
            "Search configuration and matched search terms are never copied."
        )
    )
    parser.add_argument("--input", required=True, help="Path to the Watcher results.json file")
    parser.add_argument(
        "--select",
        action="append",
        required=True,
        metavar="DOI:<value>|PMID:<value>|TITLE:<exact title>",
        help="Select one record; repeat for each citation",
    )
    parser.add_argument("--output", required=True, help="New CSV path; existing files are never overwritten")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    path = export_selected_citations(args.input, args.select, args.output)
    print(f"Exported selected citation metadata to {path}")


if __name__ == "__main__":
    main()
