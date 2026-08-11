# TODO

## Preprint → published-version linking

A bioRxiv/medRxiv/chemRxiv preprint and its eventual journal publication (e.g. JACS)
are separate DOIs, so the weekly digest can notify about the same underlying paper
twice, months apart. CrossRef exposes preprint/published relations (e.g.
`relation.is-preprint-of` on the published record) that could be used to detect this
and either suppress the second notification or annotate it (e.g. "this preprint is
now published in JACS").

## Smarter digest ranking/grouping

Weekly digest volume can run 100+ items, which is a lot to scan over coffee. Group
the email by topic/source, or surface papers matching multiple keywords first as a
relevance signal — `search_keyword`/keyword frequency data already exists per paper
and could drive this.
