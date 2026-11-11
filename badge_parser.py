"""Parse earned skill badges from a Google Skills public profile page.

How the page is structured (observed on the reference profile): every earned badge
is a link to  /public_profiles/<profile-id>/badges/<badge-id>  followed by the badge
title and the text "Earned <Mon D, YYYY> <TZ>". We therefore anchor on those badge
links (not on the word "badge"), group them by badge id, and read the title/date from
the smallest surrounding element that holds only that one badge.

The parser is covered by deterministic HTML fixtures and a mocked end-to-end scraper
regression test. If Google changes the markup, update BADGE_HREF_RE / _find_card and
run `python scripts/check_live_reference.py` when network access is available.
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup, FeatureNotFound

import config

BADGE_HREF_RE = re.compile(r"/public_profiles/([0-9a-fA-F-]{36})/badges/(\d+)")
PROFILE_ID_RE = re.compile(r"/public_profiles/([0-9a-fA-F-]{36})")
_DATE = r"[A-Z][a-z]+\.?\s+\d{1,2},\s+\d{4}"
EARNED_RE = re.compile(r"(?P<title>.*?)\s*\bEarned\s+(?P<date>" + _DATE + ")", re.S)
EARNED_ANY_RE = re.compile(r"\bEarned\s+" + _DATE)


def normalize_title(title):
    """Case/whitespace-insensitive key used for de-duplication and required-badge matching."""
    return re.sub(r"\s+", " ", title or "").strip().casefold()


def _to_iso(date_text):
    clean = (date_text or "").replace(".", "")
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(clean, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _badge_keys(tag):
    """Set of (profile_id, badge_id) for every badge link at or under `tag`."""
    keys = set()
    nodes = [tag] + tag.find_all("a", href=True) if tag.name != "a" else [tag]
    for n in nodes:
        href = n.get("href") if hasattr(n, "get") else None
        m = BADGE_HREF_RE.search(href or "")
        if m:
            keys.add((m.group(1).lower(), m.group(2)))
    return keys


def _find_card(anchor):
    """Smallest ancestor of `anchor` that contains an 'Earned <date>' string and no other badge."""
    own = _badge_keys(anchor)
    node = anchor
    while True:
        if EARNED_ANY_RE.search(node.get_text(" ", strip=True)):
            return node
        parent = node.parent
        if parent is None or parent.name in ("body", "html", "[document]"):
            return node
        if _badge_keys(parent) - own:      # parent already holds another badge -> stop
            return node
        node = parent


def _extract_entry(links, badge_id):
    for a in links:
        card = _find_card(a)
        text = " ".join(card.stripped_strings)
        m = EARNED_RE.search(text)
        title, raw_date = None, None
        if m:
            title, raw_date = m.group("title").strip(), m.group("date")
        elif card.get_text(strip=True) and len(text) < 300:
            title = next(iter(card.stripped_strings), None)
        if not title:
            img = a.find("img")
            title = (a.get("aria-label") or a.get("title") or (img.get("alt") if img else None) or "").strip()
        if title or raw_date:
            return {"title": title or f"Badge #{badge_id}", "earned_date": _to_iso(raw_date),
                    "earned_text": raw_date, "badge_id": badge_id, "title_found": bool(title)}
    return {"title": f"Badge #{badge_id}", "earned_date": None, "earned_text": None,
            "badge_id": badge_id, "title_found": False}


def _make_soup(markup):
    """Parse markup with lxml when available, otherwise use Python's built-in parser.

    The fallback is important on fresh Windows/Python installations where the optional
    lxml wheel may not have been installed yet. Both parsers preserve the anchor-based
    badge detection used below.
    """
    try:
        return BeautifulSoup(markup, "lxml")
    except FeatureNotFound:
        return BeautifulSoup(markup, "html.parser")


def _metadata_profile_id(soup):
    """Return the profile UUID declared by canonical/OG metadata, if present."""
    for tag in (soup.find("link", rel="canonical"), soup.find("meta", attrs={"property": "og:url"})):
        value = (tag.get("href") or tag.get("content")) if tag else None
        match = PROFILE_ID_RE.search(value or "")
        if match:
            return match.group(1).lower()
    return None


def _profile_name(soup):
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(" ", strip=True)
    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        return re.sub(r"\s*\|\s*Google Skills\s*$", "", og["content"]).strip() or None
    return None


def _owner_id(soup, expected, found_keys):
    metadata_id = _metadata_profile_id(soup)
    if metadata_id:
        return metadata_id
    if expected:
        return expected.lower()
    ids = [pid for pid, _ in found_keys]
    return max(set(ids), key=ids.count) if ids else None


def parse_profile(html, expected_profile_id=None):
    """Return {profile_name, badge_count, badges, status, error}.

    status is "SUCCESS" or "NEEDS REVIEW". A page whose layout is not recognised is never
    reported as zero badges.
    """
    result = {"profile_name": None, "badge_count": None, "badges": [],
              "status": config.NEEDS_REVIEW, "error": None}
    if not html or not html.strip():
        result["error"] = "Empty page returned."
        return result

    soup = _make_soup(html)
    result["profile_name"] = _profile_name(soup)
    expected = expected_profile_id.lower() if expected_profile_id else None
    metadata_id = _metadata_profile_id(soup)
    if expected and metadata_id and metadata_id != expected:
        result["error"] = (f"Profile identity mismatch: requested {expected}, "
                           f"but the page identifies itself as {metadata_id}.")
        return result

    grouped = {}   # (profile_id, badge_id) -> [anchor, ...]  (document order)
    for a in soup.find_all("a", href=True):
        m = BADGE_HREF_RE.search(a["href"])
        if m:
            grouped.setdefault((m.group(1).lower(), m.group(2)), []).append(a)

    found_profile_ids = {profile_id for profile_id, _ in grouped}
    if expected and found_profile_ids and expected not in found_profile_ids and not metadata_id:
        other = ", ".join(sorted(found_profile_ids))
        result["error"] = (f"Profile identity mismatch: the page's badge links belong to "
                           f"{other}, not the requested profile {expected}.")
        return result

    # A zero-badge result is accepted only when the page identity is independently
    # anchored by canonical/OG metadata. Otherwise a changed page or redirect could
    # be mistaken for a genuine profile with zero badges.
    identity_confirmed = bool(
        (expected and metadata_id == expected)
        or (expected and expected in found_profile_ids)
        or (not expected and (metadata_id or found_profile_ids))
    )
    owner = _owner_id(soup, expected, grouped)
    mine = {k: v for k, v in grouped.items() if owner is None or k[0] == owner}

    badges, seen = [], set()
    for (_, badge_id), links in mine.items():
        entry = _extract_entry(links, badge_id)
        key = normalize_title(entry["title"]) if entry["title_found"] else f"id:{badge_id}"
        if key in seen:            # same badge repeated (responsive markup / re-earned)
            continue
        seen.add(key)
        badges.append(entry)

    page_text = soup.get_text(" ", strip=True)
    looks_like_profile = bool(soup.find("h1")) and bool(re.search(r"Member since|League|\bpoints\b", page_text))

    if badges and identity_confirmed:
        result.update(status=config.SUCCESS, badges=badges, badge_count=len(badges))
    elif looks_like_profile and identity_confirmed:
        result.update(status=config.SUCCESS, badges=[], badge_count=0)
    elif not identity_confirmed:
        result["error"] = ("Could not confirm that the returned page belongs to the requested "
                           "Google Skills profile. The page may have redirected or its identity metadata changed.")
    else:
        result["error"] = ("Profile layout not recognised (no badge links and no profile header). "
                           "The profile may be private, require sign-in, or the page format changed.")
    return result
