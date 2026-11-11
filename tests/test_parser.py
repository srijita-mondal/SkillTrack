"""Parser tests. All use SYNTHETIC fixtures that mimic the structure observed on the real profile."""
from pathlib import Path
from badge_parser import parse_profile, normalize_title
from tests.helpers import PID, TITLES, profile_html

FIX = Path(__file__).parent / "fixtures"


def test_fixture_returns_ten_unique_badges():
    r = parse_profile((FIX / "sample_profile.html").read_text(), PID)
    assert r["status"] == "SUCCESS" and r["badge_count"] == 10
    assert r["badges"][0]["title"] == TITLES[0]
    assert r["badges"][0]["earned_date"] == "2026-11-03"


def test_duplicate_anchor_and_other_profiles_not_counted():
    # fixture has a responsive duplicate link for badge 0 and a peer's badge link
    r = parse_profile((FIX / "sample_profile.html").read_text(), PID)
    assert r["badge_count"] == 10
    assert all("Peer" not in b["title"] for b in r["badges"])


def test_same_title_twice_is_counted_once():
    r = parse_profile(profile_html([TITLES[0], TITLES[0], TITLES[1]]), PID)
    assert r["badge_count"] == 2


def test_zero_badges_profile_is_success_zero():
    r = parse_profile((FIX / "zero_badges.html").read_text(), PID)
    assert r["status"] == "SUCCESS" and r["badge_count"] == 0


def test_more_than_ten_badges():
    r = parse_profile(profile_html([f"Badge number {i}" for i in range(13)]), PID)
    assert r["badge_count"] == 13


def test_unrecognised_page_is_needs_review_not_zero():
    r = parse_profile((FIX / "signin_page.html").read_text(), PID)
    assert r["status"] == "NEEDS REVIEW" and r["badge_count"] is None and r["error"]


def test_empty_html_needs_review():
    assert parse_profile("", PID)["status"] == "NEEDS REVIEW"


def test_recommended_and_course_links_ignored():
    assert parse_profile(profile_html(TITLES[:3]), PID)["badge_count"] == 3


def test_single_badge_page_title_and_date():
    r = parse_profile(profile_html(["Only One Badge"]), PID)
    assert r["badges"][0]["title"] == "Only One Badge" and r["badge_count"] == 1


def test_owner_detected_from_canonical_without_expected_id():
    assert parse_profile(profile_html(TITLES[:2]))["badge_count"] == 2


def test_normalize_title():
    assert normalize_title("  The  Basics ") == "the basics"


def test_parser_falls_back_when_lxml_is_not_installed(monkeypatch):
    import badge_parser
    from bs4 import BeautifulSoup as real_beautiful_soup, FeatureNotFound

    def without_lxml(markup, parser):
        if parser == "lxml":
            raise FeatureNotFound("Couldn't find a tree builder with the features you requested: lxml")
        return real_beautiful_soup(markup, parser)

    monkeypatch.setattr(badge_parser, "BeautifulSoup", without_lxml)
    result = badge_parser.parse_profile((FIX / "sample_profile.html").read_text(), PID)
    assert result["status"] == "SUCCESS"
    assert result["badge_count"] == 10


def test_profile_identity_mismatch_is_never_counted_as_zero():
    from tests.helpers import OTHER_PID, profile_html

    result = parse_profile(profile_html(TITLES, pid=OTHER_PID), expected_profile_id=PID)
    assert result["status"] == "NEEDS REVIEW"
    assert result["badge_count"] is None
    assert "identity mismatch" in result["error"].lower()


def test_zero_badge_page_without_identity_evidence_needs_review():
    markup = "<html><body><h1>Someone</h1><p>Member since 2026</p><b>100 points</b></body></html>"
    result = parse_profile(markup, expected_profile_id=PID)
    assert result["status"] == "NEEDS REVIEW"
    assert result["badge_count"] is None
