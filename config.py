"""Central configuration for SkillTrack. Edit values here or override them in the app sidebar."""

APP_NAME = "SkillTrack"
APP_SUBTITLE = "Google Skills Badge Verification Dashboard"
CAMPAIGN_NAME = "Learn With Communities"
APP_VERSION = "1.2.0"

# ---- Campaign rules -------------------------------------------------------
REQUIRED_BADGES = 10          # number of unique earned skill badges needed
MODE_COUNT = "COUNT"          # any N unique earned skill badges qualify
MODE_REQUIRED = "REQUIRED_BADGES"  # only the listed campaign badge titles qualify

# ---- Upload limits --------------------------------------------------------
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB; also configured in .streamlit/config.toml

# ---- Scraper / rate limiting ---------------------------------------------
REQUEST_DELAY = 1.75          # seconds between requests (be polite)
REQUEST_TIMEOUT = 20          # seconds
MAX_RETRIES = 3               # retries for temporary failures (429/5xx/network)
BACKOFF_BASE = 2.0            # backoff = BACKOFF_BASE * 2**attempt seconds
MAX_RETRY_AFTER = 120         # never sleep longer than this for Retry-After
CHECK_ROBOTS = True           # honour robots.txt (fails open if robots.txt is unreachable)
USER_AGENT_TOKEN = "SkillTrack"
USER_AGENT = f"SkillTrack/{APP_VERSION} (campaign badge verification; polite, sequential requests)"

ALLOWED_HOSTS = {
    "skills.google", "www.skills.google",
    "cloudskillsboost.google", "www.cloudskillsboost.google",
}

# ---- Status vocabulary ----------------------------------------------------
COMPLETED = "COMPLETED"
IN_PROGRESS = "IN PROGRESS"
NOT_STARTED = "NOT STARTED"
UNAVAILABLE = "UNAVAILABLE"
INVALID_URL = "INVALID URL"
RATE_LIMITED = "RATE LIMITED"
NEEDS_REVIEW = "NEEDS REVIEW"
SCRAPING_ERROR = "SCRAPING ERROR"
PENDING = "PENDING"           # not verified yet (UI only)
SUCCESS = "SUCCESS"           # scraper-level status: profile read OK

STATUS_COLORS = {
    COMPLETED: "#16866f", IN_PROGRESS: "#c58a32", NOT_STARTED: "#71838a",
    UNAVAILABLE: "#c45f59", INVALID_URL: "#c45f59", RATE_LIMITED: "#bd762d",
    NEEDS_REVIEW: "#6b7880", SCRAPING_ERROR: "#b94e4e", PENDING: "#9aa9a8",
}

STATUS_DESCRIPTIONS = {
    COMPLETED: "The profile was verified and meets the campaign badge requirement.",
    IN_PROGRESS: "The profile was verified, but it has not earned enough qualifying badges yet.",
    NOT_STARTED: "The profile was verified and currently has no qualifying earned badges.",
    PENDING: "This profile has not been checked in the current session.",
    UNAVAILABLE: "The profile is private, missing, removed, or access was denied (HTTP 401, 403, 404 or 410).",
    INVALID_URL: "The supplied link is not a supported Google Skills public-profile URL.",
    RATE_LIMITED: "Google Skills requested a slower request rate (HTTP 429). Retry after waiting.",
    NEEDS_REVIEW: "The page layout or profile identity could not be confirmed safely.",
    SCRAPING_ERROR: "A temporary network, timeout or server error prevented verification.",
}

# A second attempt is useful for transient errors and pages that may have changed.
# INVALID URL is deliberately excluded: it must be corrected in the uploaded CSV first.
RETRYABLE_STATUSES = {UNAVAILABLE, RATE_LIMITED, NEEDS_REVIEW, SCRAPING_ERROR}

# Statuses that mean "we could not determine the badge count" (never treated as zero).
UNVERIFIED_STATUSES = {UNAVAILABLE, INVALID_URL, RATE_LIMITED, NEEDS_REVIEW, SCRAPING_ERROR}
