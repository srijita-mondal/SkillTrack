"""Offline integration regression for the reference Google Skills profile.

The normal test suite must not depend on Google's availability, IP reputation or rate
limits. This exercises the same public-profile URL through the real scraper/parser stack
using the captured ten-badge structural fixture. The optional live check lives in
scripts/check_live_reference.py and can be run manually when internet access is available.
"""
from pathlib import Path

from scraper import ProfileScraper
from tests.helpers import FakeResponse, FakeSession, PID, TITLES

REF = f"https://www.skills.google/public_profiles/{PID}"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_profile.html"


def test_reference_profile_has_ten_badges():
    session = FakeSession([FakeResponse(200, FIXTURE.read_text(encoding="utf-8"), url=REF)])
    result = ProfileScraper(session=session, check_robots=False, delay=0, max_retries=0).verify(REF)

    assert result["status"] == "SUCCESS", result
    assert result["badge_count"] == 10
    assert [badge["title"] for badge in result["badges"]] == TITLES
    assert result["profile_name"] == "Reference-style Fixture"
    assert session.calls == [REF]
