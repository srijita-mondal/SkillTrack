"""Optional live smoke check for the known Google Skills reference profile.

Run manually from the project root with:
    python scripts/check_live_reference.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper import ProfileScraper

REFERENCE_URL = "https://www.skills.google/public_profiles/be556f7b-ab4b-4be7-82fb-9be45202ddd7"


def main() -> int:
    result = ProfileScraper().verify(REFERENCE_URL)
    print(f"Status: {result['status']}")
    print(f"Badge count: {result['badge_count']}")
    print(f"Profile name: {result.get('profile_name') or 'not available'}")
    if result.get("error"):
        print(f"Details: {result['error']}")
    if result["status"] != "SUCCESS" or result["badge_count"] != 10:
        print("Live check did not confirm the expected ten badges.")
        return 1
    print("Live reference check passed: ten unique earned badges detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
