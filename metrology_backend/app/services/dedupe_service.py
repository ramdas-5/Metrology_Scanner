"""
Dedupe / cache service.

The expensive step in the pipeline is the OpenRouter call. Before calling it,
we compare the normalized OCR text of the new image against the most recent
saved scans. When similarity is >= SIMILARITY_THRESHOLD (default 80%), the
scan is almost certainly the same product label - so the caller returns the
already-saved result straight from the DB and saves an API call.

Similarity is a pure-stdlib character-level ratio over whitespace-normalized,
alphanumeric-only text (difflib.SequenceMatcher). Tune SIMILARITY_THRESHOLD /
SIMILARITY_SEARCH_LIMIT in .env; a stricter strategy (token sets, vector
embeddings, image hashing) can be dropped in here without touching the router.
"""

import difflib
import re
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from app.config import settings

_WS_RE = re.compile(r"\s+")


def _token_overlap(n1: str, n2: str) -> float:
    """Cheap Jaccard-style token overlap in [0, 1]. Used as a prefilter so the
    expensive SequenceMatcher only runs on plausible candidates."""
    if not n1 or not n2:
        return 0.0
    t1 = Counter(n1.split())
    t2 = Counter(n2.split())
    if not t1 or not t2:
        return 0.0
    intersection = sum((t1 & t2).values())
    union = sum((t1 | t2).values())
    return intersection / union if union else 0.0


def normalize_text(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace - OCR noise resistant."""
    if not text:
        return ""
    alnum = re.sub(r"[^0-9A-Za-z]+", " ", text.lower())
    return _WS_RE.sub(" ", alnum).strip()


def similarity(a: str, b: str) -> float:
    """Similarity in percent (0-100) between two normalized strings."""
    if not a or not b:
        return 0.0
    return round(difflib.SequenceMatcher(None, a, b).ratio() * 100, 2)


def find_similar_scan(
    db: Session,
    raw_text: str,
    threshold: Optional[int] = None,
    limit: Optional[int] = None,
) -> tuple:
    """
    Look for an existing scan whose OCR text is >= threshold% similar.

    Returns (scan_id_or_None, best_score_percent, best_scan_id_or_None).
    best_score_percent is the top score even when below threshold, so callers
    can log near-misses.
    """
    threshold = settings.SIMILARITY_THRESHOLD if threshold is None else threshold
    limit = settings.SIMILARITY_SEARCH_LIMIT if limit is None else limit

    norm = normalize_text(raw_text)
    if not norm:
        return None, 0.0, None

    rows = (
        db.query(models.Scan.id, models.Scan.ocr_raw_text)
        .filter(models.Scan.ocr_raw_text.isnot(None), models.Scan.ocr_raw_text != "")
        .order_by(models.Scan.created_at.desc())
        .limit(limit)
        .all()
    )

    best_score = 0.0
    best_id = None
    new_tokens = set(norm.split())
    for scan_id, other_text in rows:
        other_norm = normalize_text(other_text)
        # Quick length-rejection and cheap token-overlap prefilter: only run
        # the expensive SequenceMatcher when there is real overlap. This keeps
        # the cache check in the low milliseconds even with thousands of scans.
        len_ratio = min(len(norm), len(other_norm)) / max(len(norm), len(other_norm))
        if len_ratio < 0.4:
            continue
        if _token_overlap(norm, other_norm) < 0.35:
            continue
        score = similarity(norm, other_norm)
        if score > best_score:
            best_score = score
            best_id = scan_id
        # Early exit once we pass the threshold (rows are newest-first; a
        # really similar scan can only be newer than anything later anyway).
        if best_score >= threshold:
            break

    if best_id and best_score >= threshold:
        return best_id, best_score, best_id
    return None, best_score, best_id
