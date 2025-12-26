# PubMed Journal Club Lookup Tool

Fetch PubMed papers by journal, keyword, and author filters, then generate PowerPoint slides and HTML/txt summaries.




## MOTIVAION:

I wanted to track publications formally and avoid the paranoid feeling of missing out on cool new research. Now I run this weekly in the morning over coffee!

Specifically I wanted a powerpoint output from articles-of-interest, such that I can flip through the abstracts and keep up with recent cool publications and build up a list of interesting authors. I don't like newsletters or weekly update emails because the information conveyed is usually not logged in a manner that makes it clear what one has already encountered. Altogether this makes it easier for me to __quickly__ communicate new publications to colleagues (~25 people). - APL



---


## Setup:
- Install dependencies (venv if one is into that):
  - `python -m pip install -r requirements.txt`
- Copy sample configs to your private copies, then edit them:
  - `cp config/meta.sample.yaml config/meta.yaml`
  - `cp config/journals.sample.yaml config/journals.yaml`
  - `cp config/keywords.sample.yaml config/keywords.yaml`
  - `cp config/authors.sample.yaml config/authors.yaml`
  - `cp config/dates.sample.yaml config/dates.yaml`
  - Fill in your email, journals, keywords, authors, and date ranges.
  - (Alternatively, generate fresh samples: `python -m config.config_loader --init-samples`)
- Validate your config:
  - `python -m config.config_loader --check`
- Run the tool:
  - `python 1_Journal_Lookup_Tool_v3.6.0.py`




## Configuration:
Config lives in `config/` as YAML files:
- `meta.yaml`: `email` (required, used for PubMed), `lookup_frequency` (e.g., `1 week`), `update_date`.
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




## Outputs:
- PowerPoint: `publications.pptx` (one slide per paper).
- HTML dashboard: `output.html` (interactive tables).
- Text/JSON summaries: `publications.txt`, `results.json`.
- Prompts guard against overwriting existing files.




## Running notes:
- Tested with Python 3.13.
- Dependencies are pinned in `requirements.txt`.
- Have fun, life is short!
