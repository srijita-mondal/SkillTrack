# Changelog

## 1.2.0 — 11 November 2026

### User experience
- Replaced the purple dashboard theme with a midnight-teal palette, warm neutral backgrounds and clearer status colours.
- Added Manrope/Inter typography and a subtle geometric technology pattern in page banners.
- Replaced coordinator-facing uses of “roster” with the clearer term “student list”.
- Added a concise explanation of what a student list is on the upload page.
- Added a session-only recent verification activity panel to the dashboard.
- Split verification selection into pending profiles, retry failed profiles and re-verify all profiles.
- Improved CSV upload guidance and added troubleshooting details for file and mapping errors.

### Reliability and error handling
- Normalised common CSV parser/encoding failures into actionable coordinator-facing messages.
- Kept unexpected scraper and worker exception details separate from the user-facing message.
- Added HTTP 408 retry handling and more accurate handling for removed profiles and unexpected client errors.
- Preserved the rule that unverified profiles never receive a zero-badge count.

### Validation
- Regression suite: **65 passed, 0 failed, 0 skipped**; run `python -m pytest -q` from the project root.
- Live reference check remains separate: `python scripts/check_live_reference.py`.

## 1.1.0 — 11 November 2026

### User experience
- Reworked the dashboard into a guided coordinator landing page with a prominent upload action.
- Added an always-visible upload shortcut to the sidebar.
- Added clear page descriptions, workflow guidance, status explanations and contextual help for campaign and scraper settings.
- Improved results detail layout, profile-name fallback, last-checked display and campaign analytics.
- Removed sample/demo-style upload captions and hid Streamlit's deployment chrome from the app view.

### Verification and reliability
- Added a built-in HTML parser fallback when `lxml` is unavailable.
- Added profile identity and redirect checks to prevent false zero-badge results.
- Classified HTTP 401 as UNAVAILABLE and improved redirect handling.
- Replaced the default skipped live-network pytest with a deterministic end-to-end reference-profile regression test; moved the optional live smoke check to `scripts/check_live_reference.py`.
- Added a background verification worker with safe stop-after-current-profile behaviour and resume/retry scopes.
- Added a 5 MB upload guard, stronger spreadsheet formula protection and explicit session reset controls.
- Added verification coverage metrics based on successful profile reads.

### Validation
- Automated test suite: **60 passed, 0 skipped**.
- Python source compilation: passed.
- Streamlit browser rendering was not executed in the build environment; install the project requirements and run `streamlit run app.py` for the interactive UI.
