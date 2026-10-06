# PubMed Journal Club Lookup Tool

Fetch PubMed papers by journal, keyword, and author filters, then generate PowerPoint slides and HTML/txt summaries.




## Purpose

Journal Club Publication Watcher is an open-source research monitoring tool. It
collects matching PubMed and Crossref records, keeps published articles and
preprints distinct, and produces review-friendly PowerPoint, HTML, text, and
JSON reports. Its optional weekly digest tracks previously sent records so
papers are not repeatedly emailed.



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

Preprint full-text search is much less targeted than PubMed's indexed search, so a broad `topics` list can return a lot of noise. Set an optional `preprint_topics` list in `keywords.yaml` to use a narrower keyword set just for preprint search, while keeping the full `topics` list for PubMed:

```yaml
topics:
- CRISPR
- protein engineering
- bioinorganic chemistry
- ... (broader list, used for PubMed)

preprint_topics:
- bioinorganic chemistry
- ... (narrower list, used only for preprint search)
```

Omit `preprint_topics` to just reuse `topics` for preprints too.




## Usage:

### Try a synthetic offline demo

Generate sample PowerPoint, HTML, text, JSON, and digest-preview files without
loading local configuration, contacting PubMed or CrossRef, or sending email:

```bash
python examples/demo.py
```

The demo writes to `demo-output/` and refuses to use a non-empty destination.
Open `demo-output/digest-preview.html` to see the sample digest. The records are
fictional. Choose another empty directory with `--output-dir` if needed.

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




## Optional Weekly Email Digest (GitHub Actions)

The public repository includes an inactive [workflow example](examples/workflows/weekly-digest.yml).
To use it in your own repository, copy it to
`.github/workflows/weekly-digest.yml` and add the required Actions secrets.
The example runs `main.py --auto --notify-email` on a schedule and can also be
started manually. The personal scheduled deployment is maintained separately
from this public project.

The digest separates published articles from preprints and groups papers by journal. Within each journal group, papers matching more distinct search terms appear first, with newer papers first when match counts are tied; the matched terms are shown with each paper.

**How dedup works**: each run compares found papers against `state/seen_ids.json` (identified by PMID, DOI, then a slugified title as a fallback) and emails records it has not reported before. State is updated only after a successful send. The example workflow commits this file so state survives between runs. PMIDs, DOIs, and title slugs are public identifiers; their collection can reveal publication or reading interests. If that matters for your search, run the workflow from a private repository. Don't hand-edit or delete the state file; deleting it can cause matching papers to be sent again.

### One-time setup

**1. Gmail App Password** — the sending Gmail account needs 2-Step Verification enabled, then generate one at Google Account → Security → App Passwords → scope "Mail" (a regular Gmail password will not work with SMTP here).

**2. Bundle your local config as a secret** — `config/*.yaml` stays gitignored and out of the repository. Package it as a single base64-encoded secret that the workflow decodes at run time:

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

The example schedule is `0 13 * * 1` (Monday 13:00 UTC; GitHub Actions cron is always UTC). Edit the `cron:` line to change it. You can also start a run from the Actions tab → "Weekly Publication Digest" → "Run workflow" (`workflow_dispatch`).




## Version History:
See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Running notes:
- Tested with Python 3.9+.
- Dependencies are pinned in `requirements.txt`.
- Have fun, life is short!
