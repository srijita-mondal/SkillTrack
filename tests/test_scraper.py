"""Scraper tests with mocked HTTP (no network, no real sleeping)."""
from pathlib import Path
import requests
from scraper import ProfileScraper, validate_profile_url, parse_retry_after
from tests.helpers import PID, FakeResponse, FakeSession

URL = f"https://www.skills.google/public_profiles/{PID}"
OK_HTML = (Path(__file__).parent / "fixtures" / "sample_profile.html").read_text()


def make(responses, **kw):
    sleeps = []
    s = ProfileScraper(delay=0, max_retries=kw.pop("max_retries", 2), session=FakeSession(responses),
                       check_robots=kw.pop("check_robots", False), sleep=sleeps.append, **kw)
    return s, sleeps


def test_valid_and_invalid_urls():
    assert validate_profile_url(URL + "?x=1#y")[:2] == (True, URL)
    for bad in ["", "not a url", "https://example.com/public_profiles/" + PID,
                "https://www.skills.google/catalog", "ftp://www.skills.google/public_profiles/" + PID]:
        assert validate_profile_url(bad)[0] is False


def test_invalid_url_status_and_no_request():
    s, _ = make([FakeResponse(200, OK_HTML)])
    r = s.verify("https://example.com/x")
    assert r["status"] == "INVALID URL" and r["badge_count"] is None and s.session.calls == []


def test_success_ten_badges():
    s, _ = make([FakeResponse(200, OK_HTML)])
    r = s.verify(URL)
    assert r["status"] == "SUCCESS" and r["badge_count"] == 10


def test_403_404_are_unavailable_not_zero():
    for code in (403, 404):
        s, _ = make([FakeResponse(code)])
        r = s.verify(URL)
        assert r["status"] == "UNAVAILABLE" and r["badge_count"] is None and r["http_status"] == code


def test_429_retries_then_rate_limited_and_honours_retry_after():
    s, sleeps = make([FakeResponse(429, headers={"Retry-After": "30"})], max_retries=2)
    r = s.verify(URL)
    assert r["status"] == "RATE LIMITED" and r["badge_count"] is None
    assert len(s.session.calls) == 3 and max(sleeps) >= 30


def test_429_then_success_recovers():
    s, _ = make([FakeResponse(429), FakeResponse(200, OK_HTML)])
    assert s.verify(URL)["badge_count"] == 10


def test_5xx_is_scraping_error():
    for code in (500, 502, 503):
        s, _ = make([FakeResponse(code)], max_retries=1)
        assert s.verify(URL)["status"] == "SCRAPING ERROR"


def test_timeout_and_connection_failure():
    for exc in (requests.Timeout(), requests.ConnectionError()):
        s, _ = make([exc], max_retries=1)
        r = s.verify(URL)
        assert r["status"] == "SCRAPING ERROR" and r["badge_count"] is None


def test_exponential_backoff_grows():
    s, sleeps = make([FakeResponse(503)], max_retries=3)
    s.verify(URL)
    assert sleeps == sorted(sleeps) and sleeps[-1] > sleeps[0]


def test_duplicate_urls_use_cache():
    s, _ = make([FakeResponse(200, OK_HTML)])
    s.verify(URL)
    r2 = s.verify(URL)
    assert len(s.session.calls) == 1 and r2.get("from_cache")


def test_failed_results_are_not_cached():
    s, _ = make([FakeResponse(429), FakeResponse(200, OK_HTML)], max_retries=0)
    assert s.verify(URL)["status"] == "RATE LIMITED"
    assert s.verify(URL)["status"] == "SUCCESS"


def test_unrecognised_layout_needs_review():
    s, _ = make([FakeResponse(200, "<html><body>Sign in</body></html>")])
    r = s.verify(URL)
    assert r["status"] == "NEEDS REVIEW" and r["badge_count"] is None


def test_signin_redirect_is_unavailable():
    s, _ = make([FakeResponse(200, "x", url="https://www.skills.google/users/sign_in")])
    assert s.verify(URL)["status"] == "UNAVAILABLE"


def test_robots_disallow_blocks_request():
    robots = FakeResponse(200, "User-agent: *\nDisallow: /public_profiles/")
    s, _ = make([robots, FakeResponse(200, OK_HTML)], check_robots=True)
    r = s.verify(URL)
    assert r["status"] == "NEEDS REVIEW" and len(s.session.calls) == 1


def test_throttle_waits_between_requests():
    t = [0.0]
    sleeps = []

    def fake_sleep(x):
        sleeps.append(x)
        t[0] += x

    s = ProfileScraper(delay=2, session=FakeSession([FakeResponse(200, OK_HTML)]), check_robots=False,
                       sleep=fake_sleep, clock=lambda: t[0])
    s.verify(URL)
    s.verify("https://www.skills.google/public_profiles/22222222-2222-2222-2222-222222222222")
    assert sleeps and abs(sleeps[0] - 2) < 1e-9


def test_parse_retry_after():
    assert parse_retry_after("5") == 5.0 and parse_retry_after(None) is None and parse_retry_after("junk") is None


def test_401_is_unavailable_not_a_scraping_error():
    s, _ = make([FakeResponse(401)])
    result = s.verify(URL)
    assert result["status"] == "UNAVAILABLE"
    assert result["badge_count"] is None


def test_redirect_to_another_profile_needs_review():
    other = "https://www.skills.google/public_profiles/22222222-2222-2222-2222-222222222222"
    s, _ = make([FakeResponse(200, OK_HTML, url=other)])
    result = s.verify(URL)
    assert result["status"] == "NEEDS REVIEW"
    assert result["badge_count"] is None
    assert "different profile" in result["error"].lower()


def test_http_410_is_unavailable_not_zero():
    s, _ = make([FakeResponse(410)], max_retries=0)
    result = s.verify(URL)
    assert result["status"] == "UNAVAILABLE"
    assert result["badge_count"] is None


def test_unexpected_exception_keeps_diagnostics_out_of_user_message():
    s, _ = make([], max_retries=0)

    def explode(_url):
        raise RuntimeError("internal transport detail")

    s._verify_uncached = explode
    result = s.verify(URL)
    assert result["status"] == "SCRAPING ERROR"
    assert "internal transport detail" not in result["error"]
    assert "internal transport detail" in result["technical_error"]


def test_http_408_is_retried_and_never_becomes_zero():
    s, _ = make([FakeResponse(408), FakeResponse(408)], max_retries=1)
    result = s.verify(URL)
    assert len(s.session.calls) == 2
    assert result["status"] == "SCRAPING ERROR"
    assert result["badge_count"] is None
