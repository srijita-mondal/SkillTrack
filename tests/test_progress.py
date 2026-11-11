import pandas as pd
from progress_tracker import evaluate, parse_required_titles, build_results_df, summarize
from csv_handler import build_students
from tests.helpers import TITLES


def ok(n, titles=None):
    titles = titles or [f"B{i}" for i in range(n)]
    return {"status": "SUCCESS", "badge_count": len(titles), "badges": [{"title": t} for t in titles]}


def test_count_mode_table():
    expected = {10: ("COMPLETED", 100.0), 9: ("IN PROGRESS", 90.0), 7: ("IN PROGRESS", 70.0),
                5: ("IN PROGRESS", 50.0), 1: ("IN PROGRESS", 10.0), 0: ("NOT STARTED", 0.0)}
    for n, (status, pct) in expected.items():
        ev = evaluate(ok(n))
        assert (ev["status"], ev["percent"]) == (status, pct), n


def test_more_than_ten_caps_at_100():
    ev = evaluate(ok(13))
    assert ev["status"] == "COMPLETED" and ev["percent"] == 100.0 and ev["earned"] == 13


def test_configurable_requirement():
    assert evaluate(ok(5), required_count=5)["status"] == "COMPLETED"


def test_unverified_is_never_zero():
    for st in ["UNAVAILABLE", "RATE LIMITED", "NEEDS REVIEW", "SCRAPING ERROR", "INVALID URL"]:
        ev = evaluate({"status": st, "badges": [], "badge_count": None})
        assert ev["status"] == st and ev["earned"] is None and ev["percent"] is None


def test_no_result_is_pending():
    assert evaluate(None)["status"] == "PENDING"


def test_required_badges_mode_all_present():
    ev = evaluate(ok(0, TITLES), mode="REQUIRED_BADGES", required_titles=TITLES[:3])
    assert ev["status"] == "COMPLETED" and ev["earned"] == 3


def test_required_mode_differs_from_count_mode():
    r = ok(0, [f"Other {i}" for i in range(10)])
    assert evaluate(r)["status"] == "COMPLETED"                       # count mode: any 10
    ev = evaluate(r, mode="REQUIRED_BADGES", required_titles=["A", "B"])
    assert ev["status"] == "NOT STARTED" and ev["missing_titles"] == ["A", "B"]


def test_required_mode_partial_and_case_insensitive():
    ev = evaluate(ok(0, ["alpha", "X"]), mode="REQUIRED_BADGES", required_titles=["ALPHA", "Beta"])
    assert ev["status"] == "IN PROGRESS" and ev["percent"] == 50.0


def test_required_mode_without_titles_needs_review():
    assert evaluate(ok(3), mode="REQUIRED_BADGES", required_titles=[])["status"] == "NEEDS REVIEW"


def test_parse_required_titles_dedupes():
    assert parse_required_titles(" A \n\na\nB") == ["A", "B"]


def test_results_df_and_summary():
    base = "https://www.skills.google/public_profiles/"
    urls = [base + "a" * 8 + "-aaaa-aaaa-aaaa-" + "a" * 12, "bad", base + "b" * 8 + "-bbbb-bbbb-bbbb-" + "b" * 12]
    st = build_students(pd.DataFrame({"u": urls}), {"url": "u"})
    df = build_results_df(st, {st.loc[0, "Profile URL"]: ok(10)})
    assert list(df["Status"]) == ["COMPLETED", "INVALID URL", "PENDING"]
    s = summarize(df)
    assert (s["total"], s["completed"], s["unverified"], s["pending"]) == (3, 1, 1, 1)


def test_google_skills_name_fills_missing_roster_name():
    url = "https://www.skills.google/public_profiles/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    students = build_students(pd.DataFrame({"Profile URL": [url]}), {"url": "Profile URL"})
    raw = {url: {"status": "SUCCESS", "profile_name": "Google Profile Name", "badges": [], "checked_at": "2026-11-11 00:00 UTC"}}
    result = build_results_df(students, raw)
    assert result.loc[0, "Student Name"] == "Google Profile Name"
    assert result.loc[0, "Google Skills Name"] == "Google Profile Name"


def test_summary_includes_verified_coverage_rates():
    df = pd.DataFrame({"Status": ["COMPLETED", "IN PROGRESS", "INVALID URL", "PENDING"]})
    summary = summarize(df)
    assert summary["verified"] == 2
    assert summary["verification_rate_pct"] == 50.0
    assert summary["completion_rate_pct"] == 25.0


def test_verification_coverage_uses_profile_read_flag_not_campaign_status():
    df = pd.DataFrame({"Status": ["NEEDS REVIEW", "INVALID URL"], "Profile Verified": [True, False]})
    summary = summarize(df)
    assert summary["verified"] == 1
    assert summary["verification_rate_pct"] == 50.0
    assert summary["unverified"] == 2
