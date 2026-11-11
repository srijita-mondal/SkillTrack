"""HTTP layer: URL validation, polite fetching, retries, caching, optional Playwright fallback."""
import email.utils
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

import config
from badge_parser import parse_profile

PROFILE_PATH_RE = re.compile(r"^/public_profiles/([0-9a-fA-F-]{36})/?$")
RETRYABLE = {408, 429, 500, 502, 503, 504}


def validate_profile_url(raw):
    """Return (is_valid, normalized_url, error_message). Query strings/fragments are dropped."""
    raw = (raw or "").strip()
    if not raw:
        return False, "", "Empty URL"
    if "://" not in raw and raw.lower().startswith(("www.", "skills.google", "cloudskillsboost")):
        raw = "https://" + raw
    p = urlparse(raw)
    if p.scheme not in ("http", "https"):
        return False, raw, "URL must start with http:// or https://"
    host = (p.hostname or "").lower()
    if host not in config.ALLOWED_HOSTS:
        return False, raw, "Not a Google Skills URL (expected skills.google)"
    m = PROFILE_PATH_RE.match(p.path)
    if not m:
        return False, raw, "Not a public profile URL (expected /public_profiles/<id>)"
    return True, f"https://{host}/public_profiles/{m.group(1).lower()}", None


def parse_retry_after(value):
    """Seconds to wait from a Retry-After header (integer seconds or HTTP date); None if unusable."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(value)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError):
        return None


def make_result(url, status, error=None, http_status=None, parsed=None, technical_error=None):
    parsed = parsed or {}
    ok = status == config.SUCCESS
    return {
        "url": url, "status": status, "error": error, "technical_error": technical_error,
        "http_status": http_status,
        "profile_name": parsed.get("profile_name"),
        "badge_count": parsed.get("badge_count") if ok else None,   # never 0 for unverified
        "badges": parsed.get("badges", []) if ok else [],
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def render_with_playwright(url, timeout_ms=30000):
    """Optional fallback for JavaScript-rendered pages. Requires `pip install playwright`
    and `playwright install chromium`. Does not bypass logins, CAPTCHAs or access controls."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed.") from exc
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(user_agent=config.USER_AGENT)
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            return page.content()
        finally:
            browser.close()


class ProfileScraper:
    def __init__(self, delay=config.REQUEST_DELAY, timeout=config.REQUEST_TIMEOUT,
                 max_retries=config.MAX_RETRIES, session=None, use_playwright=False,
                 check_robots=config.CHECK_ROBOTS, sleep=time.sleep, clock=time.monotonic):
        self.delay, self.timeout, self.max_retries = delay, timeout, max_retries
        self.use_playwright, self.check_robots = use_playwright, check_robots
        self.session = session or requests.Session()
        if hasattr(self.session, "headers"):
            self.session.headers.update({"User-Agent": config.USER_AGENT, "Accept": "text/html",
                                         "Accept-Language": "en"})
        self._sleep, self._clock = sleep, clock
        self._last_request = None
        self._cache, self._robots = {}, {}

    # ---- politeness ------------------------------------------------------
    def _throttle(self):
        if self._last_request is not None:
            wait = self.delay - (self._clock() - self._last_request)
            if wait > 0:
                self._sleep(wait)

    def _robots_allows(self, url):
        if not self.check_robots:
            return True
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self._robots:
            rp = None
            try:
                r = self.session.get(base + "/robots.txt", timeout=self.timeout)
                if r.status_code == 200:
                    rp = RobotFileParser()
                    rp.parse(r.text.splitlines())
            except requests.RequestException:
                rp = None                      # fail open: robots.txt unreachable
            self._robots[base] = rp
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(config.USER_AGENT_TOKEN, url)

    # ---- fetching with retries ------------------------------------------
    def _get(self, url):
        """Return (response, error_kind). error_kind is None on HTTP 200."""
        resp, kind = None, "network"
        for attempt in range(self.max_retries + 1):
            self._throttle()
            retry_after = None
            try:
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                self._last_request = self._clock()
                if resp.status_code == 200:
                    return resp, None
                if resp.status_code not in RETRYABLE:
                    return resp, "http"
                kind = "http"
                retry_after = parse_retry_after(resp.headers.get("Retry-After"))
            except requests.Timeout:
                self._last_request, resp, kind = self._clock(), None, "timeout"
            except requests.ConnectionError:
                self._last_request, resp, kind = self._clock(), None, "connection"
            except requests.RequestException:
                self._last_request, resp, kind = self._clock(), None, "network"
            if attempt < self.max_retries:
                wait = config.BACKOFF_BASE * (2 ** attempt)
                if retry_after is not None:
                    wait = max(wait, min(retry_after, config.MAX_RETRY_AFTER))
                self._sleep(wait)
        return resp, kind

    # ---- public API ------------------------------------------------------
    def verify(self, raw_url):
        """Fetch and parse one profile. Always returns a result dict (never raises)."""
        ok, url, err = validate_profile_url(raw_url)
        if not ok:
            return make_result(raw_url, config.INVALID_URL, err)
        if url in self._cache:
            return dict(self._cache[url], from_cache=True)
        try:
            result = self._verify_uncached(url)
        except Exception as exc:  # one unexpected profile failure must not stop a run
            result = make_result(
                url, config.SCRAPING_ERROR,
                "An unexpected problem occurred while checking this profile. Retry it later; "
                "if the problem continues, contact the application administrator.",
                technical_error=f"{type(exc).__name__}: {exc}",
            )
        if result["status"] not in (config.RATE_LIMITED, config.SCRAPING_ERROR):
            self._cache[url] = result          # temporary failures are retried on the next run
        return result

    def _verify_uncached(self, url):
        if not self._robots_allows(url):
            return make_result(url, config.NEEDS_REVIEW, "robots.txt disallows automated access to this page.")
        resp, kind = self._get(url)
        if kind is not None:
            code = resp.status_code if resp is not None else None
            if kind == "timeout":
                return make_result(url, config.SCRAPING_ERROR, "Request timed out after retries.")
            if kind in ("connection", "network"):
                return make_result(url, config.SCRAPING_ERROR, "Network/connection failure after retries.")
            if code == 429:
                return make_result(url, config.RATE_LIMITED, "HTTP 429: rate limited. Increase the delay and retry later.", code)
            if code == 401:
                return make_result(url, config.UNAVAILABLE, "HTTP 401: authentication is required; only public profiles can be verified.", code)
            if code == 403:
                return make_result(url, config.UNAVAILABLE, "HTTP 403: access denied (profile may be private or blocked).", code)
            if code in (404, 410):
                return make_result(url, config.UNAVAILABLE, f"HTTP {code}: profile not found or no longer available.", code)
            if code == 408:
                return make_result(url, config.SCRAPING_ERROR, "The website timed out while processing the request. Please retry later.", code)
            if code is not None and 400 <= code < 500:
                return make_result(
                    url, config.NEEDS_REVIEW,
                    f"The website rejected this request (HTTP {code}). Check the profile link and retry later; no badge count was recorded.",
                    code,
                )
            return make_result(url, config.SCRAPING_ERROR, f"The website returned an unsuccessful response (HTTP {code}). No badge count was recorded.", code)

        final_url = getattr(resp, "url", "") or ""
        if "sign_in" in final_url.lower() or "/users/sign_in" in final_url.lower():
            return make_result(url, config.UNAVAILABLE, "Redirected to sign-in: profile is private.", 200)

        profile_id = url.rsplit("/", 1)[-1]
        if final_url:
            final_ok, final_normalized, final_error = validate_profile_url(final_url)
            if not final_ok:
                return make_result(
                    url, config.NEEDS_REVIEW,
                    f"The request redirected to an unexpected page ({final_error}). Verify the profile link manually.", 200,
                )
            final_profile_id = final_normalized.rsplit("/", 1)[-1]
            if final_profile_id != profile_id:
                return make_result(
                    url, config.NEEDS_REVIEW,
                    f"The request redirected to a different profile ({final_profile_id}); no badge count was recorded.", 200,
                )

        parsed = parse_profile(resp.text, expected_profile_id=profile_id)
        if parsed["status"] != config.SUCCESS and self.use_playwright:
            try:
                parsed = parse_profile(render_with_playwright(url), expected_profile_id=profile_id)
            except Exception as exc:
                parsed["error"] = f"{parsed['error']} Playwright fallback failed: {exc}"
        return make_result(url, parsed["status"], parsed["error"], 200, parsed)
