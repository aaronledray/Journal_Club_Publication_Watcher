# Changelog

All notable changes to the Journal Club Publication Watcher project will be documented in this file.

## [3.9.0] - 2026-08-11

### Added
- Keyword-based preprint server watching (bioRxiv, medRxiv, chemRxiv, ...) via new `preprint_servers` field in `meta.yaml`, searched through CrossRef's `posted-content` records using the existing `topics` keywords
- `search_preprints_by_keywords()` in `fetch_modules/crossref_client.py`, with per-server matching (institution-name for bioRxiv/medRxiv, DOI-prefix for chemRxiv since it doesn't populate CrossRef's institution field)

### Fixed
- `extract_crossref_journal()` now falls back to the preprint server name when `container-title` is absent, instead of showing "No journal available" for every preprint

## [3.8.0] - 2026-08-05

### Added
- Weekly email digest via `--notify-email` flag, sent over Gmail SMTP
- GitHub Actions workflow (`.github/workflows/weekly-digest.yml`) to run the digest on a weekly cron schedule
- Cross-run "seen papers" tracking (`state/seen_ids.json`, `notify_modules/seen_tracker.py`) so digests only include papers not already reported, keyed by PMID/DOI/title
- `PMID` field on PubMed-sourced paper components

## [3.6.0] - 2024-12-26

### Added
- Refactored codebase with modular architecture
- Added HTML dashboard output with interactive tables
- Added JSON output for results
- Command-line argument parsing (--auto, --mode, --config-dir, --output-dir)
- Configuration validation with helpful error messages

### Changed
- Migrated to YAML-based configuration system
- Improved code organization with separate modules for fetching, processing, and output

## [3.3.0] - 2024-11-29/30

### Changed
- Novel keywords slide: text now smaller
- Text-only output with exhaustive printing and prettier formatting
- Embedded text outputter into main workflow

## [3.2.0] - 2024-08-28 to 2024-09-20

### Added
- Authors section in config with ORCID support
- Keyword "clustered" mode (inclusive mode)
- Blank line feature for all sub-topic search support

### Changed
- Updated config file formatting with headers

### Fixed
- Fixed the keyword hit table slide in PowerPoint output

## [3.1.0] - 2024-07-31 to 2024-08-14

### Added
- User prompt before overwriting existing PowerPoint files
- Keywords extraction added to paper dictionary
- Full author names (first and last) in PowerPoint and other outputs
- Option to open all DOI links in Safari browser windows

### Changed
- Author name format now includes first and last name, not just last

## [3.0.1] - 2024-07-10

### Added
- Re-incorporated sleep(1) between Entrez requests to prevent XML errors

### Changed
- Improved formatting for slides by reducing title character limit
- PowerPoint now displays current date instead of '3000' when using current date

## [3.0.0] - 2024-07-10

### Changed
- Major refactoring by Lisa P.
- Adapted Entrez query error handling from [Stack Overflow solution](https://stackoverflow.com/questions/75678873/unpredictable-httperror-using-entrez-esearch-function-from-bio-package)

---

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
