# PubMed Journal Club Lookup Tool

Fetch PubMed papers by journal, keyword, and author filters, then generate PowerPoint slides and HTML/txt summaries.




## Motivation:

I wanted to track publications formally and avoid the paranoid feeling of missing out on cool new research. Now I run this weekly in the morning over coffee!

Specifically I wanted a powerpoint output from articles-of-interest, such that I can flip through the abstracts and keep up with recent cool publications and build up a list of interesting authors. I don't like newsletters or weekly update emails because the information conveyed is usually not logged in a manner that makes it clear what one has already encountered. Altogether this makes it easier for me to __quickly__ communicate new publications to colleagues (~25 people). - APL



---


## Setup:

```bash
# Install dependencies
pip install -r requirements.txt

# Copy sample configs and edit them
cp config/meta.sample.yaml config/meta.yaml
cp config/journals.sample.yaml config/journals.yaml
cp config/keywords.sample.yaml config/keywords.yaml
cp config/authors.sample.yaml config/authors.yaml
cp config/dates.sample.yaml config/dates.yaml

# Edit config files with your details (in config/ directory)

# Validate your config
python -m config.config_loader --check

# Run the tool
python main.py
```




## Configuration:
Config lives in `config/` as YAML files:
- `meta.yaml`: `email` (required, used for PubMed), `lookup_frequency` (e.g., `1 week`), `update_date`, `preprint_servers` (optional, e.g. `[bioRxiv, medRxiv, chemRxiv]`).
- `journals.yaml`: `journals: [ ... ]` list of journal names.
- `keywords.yaml`: `topics: [ ... ]` list of keywords.
- `authors.yaml`: `authors: [ ... ]` list of ORCIDs, optionally with names (`0000-0000-0000-0000 # Jane Doe`).
- `dates.yaml`: `date_ranges: [[YYYY/MM/DD, YYYY/MM/DD], ...]` optional explicit ranges.

Create starter files. Two options:
- Use the included `*.sample.yaml` files and copy them as shown above, or
- Run `python -m config.config_loader --init-samples` (does not overwrite existing files).

Validate any time:
- `python -m config.config_loader --check`
- Fails fast on missing email, empty journal/keyword lists, invalid dates, or bad lookup_frequency formatting.

### Preprint servers (bioRxiv, medRxiv, chemRxiv, ...)

Set `preprint_servers` in `meta.yaml` to also search preprint servers using the same `topics` keywords:

```yaml
preprint_servers:
- bioRxiv
- medRxiv
- chemRxiv
```

This runs alongside the normal PubMed keyword search (only in `--mode keywords`/`both`) via CrossRef's `posted-content` records, since bioRxiv/medRxiv/chemRxiv all register their DOIs with CrossRef. Results are tagged with the matched server as their `Source`/`Journal`. Omit `preprint_servers` (or leave it empty) to skip preprint search entirely — it's off by default.




## Usage:

```bash
# Interactive mode (default)
python main.py

# Automatic mode (non-interactive)
python main.py --auto

# Search only by keywords
python main.py --mode keywords

# Search only by authors/ORCIDs
python main.py --mode authors

# Custom config and output directories
python main.py --config-dir /path/to/config --output-dir /path/to/output

# Send a weekly email digest of newly-found papers (see "Weekly Email Digest" below)
python main.py --auto --notify-email
```

## Outputs:
- PowerPoint: `publications.pptx` (one slide per paper).
- HTML dashboard: `publications.html` (interactive tables).
- Text/JSON summaries: `publications.txt`, `results.json`.
- Confirms with user before overwriting existing files.




## Weekly Email Digest (GitHub Actions):

A GitHub Actions workflow (`.github/workflows/weekly-digest.yml`) runs `main.py --auto --notify-email` on a schedule in the cloud, so you get a weekly email of newly-published papers without needing your own machine to be on.

**How dedup works**: each run compares found papers against `state/seen_ids.json` (identified by PMID, then DOI, then a slugified title as a fallback) and only emails ones it hasn't reported before, then commits the updated state file back to the repo. This file only stores PMIDs/DOIs/title-slugs — no personal data — so it's safe to keep tracked in the public repo. Don't hand-edit or delete it; deleting it will cause every currently-matching paper to be re-sent once.

### One-time setup

**1. Gmail App Password** — the sending Gmail account needs 2-Step Verification enabled, then generate one at Google Account → Security → App Passwords → scope "Mail" (a regular Gmail password will not work with SMTP here).

**2. Bundle your personal config as a secret** — `config/*.yaml` (your keywords, journals, ORCIDs) stays gitignored and out of the public repo. Instead, package it as a single base64-encoded secret the workflow decodes at run time:

```bash
tar -czf /tmp/config-bundle.tar.gz -C config meta.yaml journals.yaml keywords.yaml authors.yaml dates.yaml
base64 -i /tmp/config-bundle.tar.gz -o /tmp/config-bundle.b64   # Linux: base64 -w0 ... > ...
gh secret set CONFIG_BUNDLE_B64 --repo <owner>/<repo> < /tmp/config-bundle.b64
rm /tmp/config-bundle.tar.gz /tmp/config-bundle.b64
```

Re-run this any time your local `config/*.yaml` files change — the secret is a point-in-time snapshot, not synced automatically.

**3. Set the remaining repo secrets** (Settings → Secrets and variables → Actions, or `gh secret set <NAME>`):
- `GMAIL_ADDRESS` — the sending Gmail address.
- `GMAIL_APP_PASSWORD` — the App Password from step 1.
- `RECIPIENT_EMAIL` — where the digest should be sent.

### Schedule and manual runs

The default schedule is `0 13 * * 1` (Monday 13:00 UTC — GitHub Actions cron is always UTC, adjust for your local time). Edit the `cron:` line in the workflow file to change it. You can also trigger a test run any time from the Actions tab → "Weekly Publication Digest" → "Run workflow" (`workflow_dispatch`).




## Version History:
See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Running notes:
- Tested with Python 3.9+.
- Dependencies are pinned in `requirements.txt`.
- Have fun, life is short!
