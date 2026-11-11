"""Synthetic HTML builders and fake HTTP objects (no network)."""
PID = "be556f7b-ab4b-4be7-82fb-9be45202ddd7"
OTHER_PID = "11111111-2222-3333-4444-555555555555"

TITLES = [
    "Explore Generative AI in Agent Platform",
    "Store, Process, and Manage Data on Google Cloud - Console",
    "Using the Google Cloud Speech API",
    "Create Your First Gemini Enterprise Application",
    "Build a Website on Google Cloud",
    "Analyze Images with the Cloud Vision API",
    "Develop AI-Powered Prototypes in Google AI Studio",
    "Implement Speech and Language Solutions with Pre-trained APIs",
    "Configure Service Accounts and IAM Roles for Google Cloud",
    "The Basics of Google Cloud Compute",
]


def badge_html(i, title, date="Nov 3, 2026 EST", pid=PID, duplicate_anchor=False):
    bid = 29000000 + i
    dup = f'<a class="mobile" href="/public_profiles/{pid}/badges/{bid}">{title}</a>' if duplicate_anchor else ""
    return (f'<div class="profile-badge"><a href="https://www.skills.google/public_profiles/{pid}/badges/{bid}">'
            f'<img src="https://cdn.example/{i}.png" alt=""></a>'
            f'<span class="ql-title-medium">{title}</span>'
            f'<span class="ql-body-medium">Earned {date}</span>{dup}</div>')


def profile_html(titles, name="Test Student", pid=PID, extra="", dup_first=False):
    badges = "".join(badge_html(i, t, duplicate_anchor=(dup_first and i == 0)) for i, t in enumerate(titles))
    return (f'<html><head><link rel="canonical" href="https://www.skills.google/public_profiles/{pid}">'
            f'<title>{name} | Google Skills</title></head><body><header><a href="/">Google Skills</a> Sign in</header>'
            f'<h1>{name}</h1><p>Member since 2026</p><h2>Silver League</h2><b>339 points</b>'
            f'<section class="badges">{badges}</section>'
            f'<section class="recommended"><a href="/catalog/badge-skill-x">Recommended skill badge</a> '
            f'<a href="/course_templates/1">Intro course</a> Earned certificate achievements</section>'
            f'{extra}</body></html>')


class FakeResponse:
    def __init__(self, status=200, text="", headers=None, url=""):
        self.status_code, self.text, self.headers, self.url = status, text, headers or {}, url


class FakeSession:
    """Returns queued responses in order (the last one repeats). A queued Exception is raised."""
    def __init__(self, responses):
        self.responses, self.calls, self.headers = list(responses), [], {}

    def get(self, url, **kw):
        self.calls.append(url)
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        return item
