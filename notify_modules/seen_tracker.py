"""
Cross-run "seen papers" tracker for email notifications.

Persists state/seen_ids.json so weekly digests only include papers not
already reported by a previous --notify-email run. The file is tracked
in git (not gitignored) since it only stores PMIDs/DOIs/title-slugs,
which aren't sensitive, and GitHub Actions needs to commit updates to
it so state survives across ephemeral runners.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_SEEN_STATE_PATH = "state/seen_ids.json"
STATE_VERSION = 1
DEFAULT_PRUNE_AFTER_DAYS = 180


def _slugify_title(title: str) -> str:
    """Normalize a title into a stable fallback identity key."""
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").strip().lower()).strip("-")
    return slug or "untitled"


def _normalize_doi(value: Any) -> str:
    """Normalize a DOI or DOI URL for stable identity comparisons."""
    if not isinstance(value, str):
        return ""
    doi = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip().rstrip(".")


def _component_dois(component: Dict[str, Any]) -> List[str]:
    """Return the component DOI plus any CrossRef-related DOI aliases."""
    dois = []
    for value in (component.get("DOI"), component.get("Link")):
        doi = _normalize_doi(value)
        if "doi.org/" in doi:
            doi = doi.split("doi.org/", 1)[1].strip("/")
        if doi and doi not in dois:
            dois.append(doi)

    related = component.get("RelatedDOIs") or {}
    if isinstance(related, dict):
        values = [value for group in related.values() for value in (group if isinstance(group, list) else [group])]
        for value in values:
            doi = _normalize_doi(value)
            if doi and doi not in dois:
                dois.append(doi)
    return dois


def get_component_ids(component: Dict[str, Any]) -> List[str]:
    """Return all identity keys, including CrossRef relation aliases.

    A PMID remains the primary key when present, but DOI keys are also kept so
    a PubMed record can match a CrossRef preprint/publication relationship.
    """
    pmid = (component.get("PMID") or "").strip()
    ids = [f"pmid:{pmid}"] if pmid else []
    ids.extend(f"doi:{doi}" for doi in _component_dois(component) if f"doi:{doi}" not in ids)
    return ids or [f"title:{_slugify_title(component.get('Title', ''))}"]


def get_component_id(component: Dict[str, Any]) -> str:
    """Return the primary identity key for compatibility with existing callers."""
    return get_component_ids(component)[0]


def load_seen_state(path: str = DEFAULT_SEEN_STATE_PATH) -> Dict[str, Any]:
    """Load state/seen_ids.json; return a fresh empty structure if absent or corrupt."""
    file_path = Path(path)
    if not file_path.exists():
        return {"version": STATE_VERSION, "seen": {}}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "seen" not in data:
            raise ValueError("malformed seen-state file")
        return data
    except (json.JSONDecodeError, ValueError) as e:
        print(f"   Warning: could not parse {path} ({e}); starting from empty state")
        return {"version": STATE_VERSION, "seen": {}}


def filter_unseen(components: List[Dict[str, Any]], seen_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return components whose primary or related identity is not seen."""
    seen_ids = seen_state.get("seen", {})
    unseen, batch_seen = [], set()
    for component in components:
        component_ids = get_component_ids(component)
        if not any(cid in seen_ids or cid in batch_seen for cid in component_ids):
            unseen.append(component)
            batch_seen.update(component_ids)
    return unseen


def mark_seen(components: List[Dict[str, Any]], seen_state: Dict[str, Any]) -> Dict[str, Any]:
    """Record identity keys for `components` with a UTC timestamp. Mutates and returns seen_state."""
    now_iso = datetime.now(timezone.utc).isoformat()
    seen_ids = seen_state.setdefault("seen", {})
    seen_state.setdefault("version", STATE_VERSION)
    for component in components:
        for cid in get_component_ids(component):
            seen_ids[cid] = now_iso
    return seen_state


def prune_old_entries(seen_state: Dict[str, Any], max_age_days: int = DEFAULT_PRUNE_AFTER_DAYS) -> Dict[str, Any]:
    """
    Drop entries older than max_age_days so the file doesn't grow forever.
    Safe because PubMed/CrossRef date-range queries only ever look a few
    weeks back (meta.yaml lookup_frequency), so an entry this old can
    never legitimately reappear as a "new" search hit.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    kept = {}
    for cid, ts in seen_state.get("seen", {}).items():
        try:
            if datetime.fromisoformat(ts) >= cutoff:
                kept[cid] = ts
        except ValueError:
            kept[cid] = ts  # keep unparseable timestamps rather than risk data loss
    seen_state["seen"] = kept
    return seen_state


def save_seen_state(seen_state: Dict[str, Any], path: str = DEFAULT_SEEN_STATE_PATH) -> None:
    """Write state as pretty, sort_keys=True JSON for small/stable git diffs."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(seen_state, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
