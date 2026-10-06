# TODO

## Preprint → published-version linking

Done: CrossRef relation metadata is carried into paper components, related
DOIs are used for email deduplication, and published-version links are shown in
the email and report outputs. Offline fixtures cover multiple and reciprocal
relations, DOI normalization, and missing relation metadata.

## Smarter digest ranking

Done: within each journal group, papers are ranked by distinct matched search
terms and then publication date. The digest shows the matched terms, and both
PubMed and CrossRef duplicate handling preserve them.

## Attach the interactive HTML dashboard to the email

Done: attach a temporary dashboard containing only new papers. Seen-state is
updated only after the digest sends successfully.

## Public demo and offline CI

Done: `examples/demo.py` generates clearly labeled synthetic reports without
loading configuration, contacting APIs, or sending email. CI runs offline tests
and the demo on Python 3.9 and 3.11.

## Reliability, privacy, and output safety

Done: configuration diagnostics no longer print configured values; digest HTML
escapes API content and accepts only HTTP(S) links; HTML attachments use a
`multipart/mixed` message containing an `alternative` body; seen-state retention
covers the configured lookup window; nested output directories are created;
README explains that public deduplication IDs can reveal reading interests.

## Public deployment boundary

In progress: the personal workflow and a copy of its state are in a private
deployment repository. Its workflow is disabled until the four
required secrets are added. The public schedule has been disabled; its workflow
is now an example under `examples/workflows/`. The public state file remains
tracked and unchanged, as required, but will no longer receive personal
updates once the code changes are merged. Add the private secrets, enable the
private workflow, then remove the now-unused secrets from the public repo.

## GitHub Actions runner incident

The October 5 run was cancelled before workflow steps started because GitHub
could not allocate a hosted runner after retries. Pinning CI and digest jobs to
`ubuntu-24.04` avoids the announced `ubuntu-latest` migration to Ubuntu 26; it
does not address transient hosted-runner capacity failures.
