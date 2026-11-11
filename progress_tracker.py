"""Turn raw scrape results into campaign status, completion percentages and summary KPIs."""
import pandas as pd

import config
from badge_parser import normalize_title


def parse_required_titles(text):
    """One title per line (blank lines ignored, duplicates removed, order kept)."""
    seen, titles = set(), []
    for line in (text or "").splitlines():
        t = line.strip()
        if t and normalize_title(t) not in seen:
            seen.add(normalize_title(t))
            titles.append(t)
    return titles


def evaluate(result, required_count=config.REQUIRED_BADGES, mode=config.MODE_COUNT, required_titles=None):
    """Campaign evaluation of one scrape result.

    Returns dict(status, earned, required, percent, missing_titles). For profiles that could not
    be verified, earned/percent are None and status is the failure status - never zero badges.
    """
    out = {"status": config.PENDING, "earned": None, "required": None, "percent": None, "missing_titles": []}
    if result is None:
        return out
    if result["status"] != config.SUCCESS:
        out["status"] = result["status"] if result["status"] in config.STATUS_COLORS else config.NEEDS_REVIEW
        out["required"] = required_count if mode == config.MODE_COUNT else len(required_titles or [])
        return out

    badges = result.get("badges", [])
    if mode == config.MODE_REQUIRED:
        wanted = parse_required_titles("\n".join(required_titles or []))
        if not wanted:
            out.update(status=config.NEEDS_REVIEW, required=0)
            return out
        have = {normalize_title(b["title"]) for b in badges}
        missing = [t for t in wanted if normalize_title(t) not in have]
        earned, required = len(wanted) - len(missing), len(wanted)
        out["missing_titles"] = missing
    else:
        # the parser already de-duplicates, but dedupe again so callers can pass any result dict
        earned, required = len({normalize_title(b["title"]) for b in badges}), required_count

    required = max(required, 1)
    out.update(earned=earned, required=required, percent=round(min(earned / required, 1) * 100, 1))
    out["status"] = config.COMPLETED if earned >= required else (config.IN_PROGRESS if earned > 0 else config.NOT_STARTED)
    return out


def build_results_df(students, raw, required_count=config.REQUIRED_BADGES,
                     mode=config.MODE_COUNT, required_titles=None):
    """Join the student table with scrape results (raw: {profile_url: result})."""
    rows = []
    for _, s in students.iterrows():
        if not s["URL Valid"]:
            res = {"status": config.INVALID_URL, "error": s["URL Error"], "badges": [], "checked_at": ""}
        else:
            res = raw.get(s["Profile URL"])
        ev = evaluate(res, required_count, mode, required_titles)
        res = res or {}
        error = res.get("error") or ""
        if ev["missing_titles"]:
            error = (error + " " if error else "") + "Missing required: " + "; ".join(ev["missing_titles"])
        google_name = res.get("profile_name") or ""
        supplied_name = s["Student Name"] or ""
        rows.append({
            "Row": s["Row"], "Student ID": s["Student ID"],
            # Prefer the coordinator-provided student name; use the verified profile name only
            # when the CSV did not supply one.
            "Student Name": supplied_name or google_name,
            "Profile URL": s["Profile URL"], "Earned Badges": ev["earned"], "Required": ev["required"],
            "Progress": ev["percent"], "Status": ev["status"],
            "Badge Titles": "; ".join(b["title"] for b in res.get("badges", [])),
            "Last Checked": res.get("checked_at", ""), "Error Message": error,
            "Duplicate Profile": bool(s["Duplicate Profile"]),
            "Profile Verified": res.get("status") == config.SUCCESS,
            "Google Skills Name": google_name,
        })
    df = pd.DataFrame(rows)
    df["Earned Badges"] = pd.array(df["Earned Badges"], dtype="Int64")
    df["Required"] = pd.array(df["Required"], dtype="Int64")
    df["Progress"] = pd.to_numeric(df["Progress"], errors="coerce")
    extras = [c for c in students.columns if c.startswith("orig: ")]
    for c in extras:
        df[c] = students[c].values
    return df


def summarize(results):
    """KPI counts. 'unverified' = could not be verified (needs attention); 'pending' = not run yet."""
    counts = results["Status"].value_counts()
    g = lambda s: int(counts.get(s, 0))
    unverified = sum(g(s) for s in config.UNVERIFIED_STATUSES)
    if "Profile Verified" in results.columns:
        verified = int(results["Profile Verified"].fillna(False).astype(bool).sum())
    else:
        verified = g(config.COMPLETED) + g(config.IN_PROGRESS) + g(config.NOT_STARTED)
    total = len(results)
    return {
        "total": total, "completed": g(config.COMPLETED), "in_progress": g(config.IN_PROGRESS),
        "not_started": g(config.NOT_STARTED), "unverified": unverified, "pending": g(config.PENDING),
        "verified": verified,
        "verification_rate_pct": round(100 * verified / total, 1) if total else 0.0,
        "completion_rate_pct": round(100 * g(config.COMPLETED) / total, 1) if total else 0.0,
    }
