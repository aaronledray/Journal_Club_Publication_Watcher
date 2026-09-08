# TODO

## Preprint → published-version linking

In progress: CrossRef relation metadata is now carried into paper components;
related DOIs are treated as aliases by email seen-state tracking, and preprints
show a published-version DOI when CrossRef provides one. Remaining work is to
add broader fixture coverage and decide whether non-email outputs should also
surface the relationship.

A bioRxiv/medRxiv/chemRxiv preprint and its eventual journal publication (e.g. JACS)
are separate DOIs, so the weekly digest can notify about the same underlying paper
twice, months apart. CrossRef exposes preprint/published relations (e.g.
`relation.is-preprint-of` on the published record) that could be used to detect this
and either suppress the second notification or annotate it (e.g. "this preprint is
now published in JACS").

## Smarter digest ranking

Done: papers are now split into Published Articles / Preprints sections (visually
distinct banners + divider) and grouped by journal within each section, ordered by
paper count. Still open: surfacing papers that match multiple keywords first as a
relevance signal — `search_keyword`/keyword frequency data already exists per paper
and could drive this.

## Attach the interactive HTML dashboard to the email

In progress: generate a new-only dashboard in a temporary directory, attach
the HTML to the digest, and remove the temporary files after sending. The
existing full-result dashboard remains unchanged.

`write_html_dashboard()` (in `output_modules/html_builder.py`) already produces a
sortable/searchable/theme-toggling dashboard as `publications.html` — likely a
better read than the email body alone. Discussed but not built. Notes for whoever
picks this up:

- Mechanically simple: add a `MIMEApplication` (or `MIMEText(..., 'html')` with
  `Content-Disposition: attachment`) part to the `MIMEMultipart` message built in
  `notify_modules/email_sender.py::send_digest_email()`. File sizes for a
  ~50-130 paper digest are a few hundred KB, well under Gmail's 25MB limit. The
  dashboard's JS/CSS loads from CDN, so it still works opened locally given
  internet access.
- Structural wrinkle: `main.py` currently sends the email *before*
  `generate_outputs()` runs (deliberately - so a failed send can't silently drop
  papers from future digests, since seen-state is only marked after a successful
  send). Attaching the dashboard means either building the HTML earlier (before
  the notify step) or moving the email send after output generation - needs
  correct sequencing either way.
- Design decision needed: should the attached dashboard scope to just the new
  (unseen) papers reported in that email, or the full week's results including
  already-seen ones (what `generate_outputs()` normally builds)? Leaning toward
  "new only" to match the email's intent, but it's a product call.
- Considered and rejected for now: hosting the HTML via GitHub Pages and emailing
  a link instead of attaching. Avoids attachment bloat over time, but adds a
  public-hosting wrinkle for what's otherwise a private personal digest. Plain
  attachment is the better fit unless that changes.
