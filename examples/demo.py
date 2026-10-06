"""Generate synthetic reports without loading config or contacting APIs."""

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from main import generate_outputs
from notify_modules.email_sender import build_html_body, build_plaintext_body


DATE_RANGE = ("2025/01/01", "2025/12/31")


def sample_components():
    """Return fictional records that demonstrate digest ranking and sections."""
    common = {
        "Authors": ["Demo Author", "Sample Researcher"],
        "Institution": ["Example Institute"],
        "Keywords": ["synthetic example"],
        "Abstract": (
            "This fictional record demonstrates report generation. It is not a "
            "real publication and was not fetched from PubMed or CrossRef."
        ),
    }

    return [
        {
            **common,
            "Title": "DEMO: A synthetic paper matching two search terms",
            "Journal": "Synthetic Journal of Examples",
            "Link": "https://example.invalid/papers/multiple-match",
            "DOI": "",
            "Date": "2025/04/15",
            "Source": "keyword",
            "IsPreprint": False,
            "MatchedKeywords": ["alpha", "beta"],
        },
        {
            **common,
            "Title": "DEMO: A synthetic paper matching one search term",
            "Journal": "Synthetic Journal of Examples",
            "Link": "https://example.invalid/papers/single-match",
            "DOI": "",
            "Date": "2025/06/10",
            "Source": "keyword",
            "IsPreprint": False,
            "MatchedKeywords": ["alpha"],
        },
        {
            **common,
            "Title": "DEMO: A synthetic preprint",
            "Journal": "Synthetic Preprint Server",
            "Link": "https://example.invalid/preprints/sample",
            "DOI": "",
            "Date": "2025/07/03",
            "Source": "Synthetic Preprint Server",
            "IsPreprint": True,
            "MatchedKeywords": ["beta", "gamma"],
        },
    ]


def run_demo(output_dir: Path) -> Path:
    """Write synthetic reports, refusing to overwrite a non-empty directory."""
    output_dir = output_dir.expanduser().resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}. Choose an empty directory."
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    papers = sample_components()
    config = {
        "journals": ["Synthetic Journal of Examples"],
        "topics": ["alpha", "beta", "gamma"],
        "named_authors": [],
        "orcids": [],
    }
    keyword_frequencies = {"alpha": 2, "beta": 2, "gamma": 1}

    generate_outputs(
        config=config,
        date_range=DATE_RANGE,
        components_keyword=papers,
        components_orcid=[],
        keyword_frequencies=keyword_frequencies,
        output_dir=str(output_dir),
        auto_mode=True,
    )

    (output_dir / "digest-preview.txt").write_text(
        build_plaintext_body(papers, DATE_RANGE), encoding="utf-8"
    )
    (output_dir / "digest-preview.html").write_text(
        build_html_body(papers, DATE_RANGE), encoding="utf-8"
    )
    (output_dir / "DEMO_README.txt").write_text(
        "Synthetic demonstration only. These records are fictional, were not "
        "fetched from PubMed or CrossRef, and were not emailed.\n",
        encoding="utf-8",
    )
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic Journal Club Publication Watcher reports. "
            "This demo uses no API, personal config, or email."
        )
    )
    parser.add_argument(
        "--output-dir",
        default="demo-output",
        help="Empty destination directory (default: demo-output)",
    )
    args = parser.parse_args()

    try:
        output_dir = run_demo(Path(args.output_dir))
    except FileExistsError as exc:
        parser.error(str(exc))

    print("Generated synthetic demo reports; no API calls or email were used.")
    print(f"Open {output_dir / 'digest-preview.html'} to view the digest preview.")
    print(f"All demo files are in: {output_dir}")


if __name__ == "__main__":
    main()
