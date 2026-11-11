# SkillTrack — Google Skills Badge Verification Dashboard

SkillTrack helps campaign coordinators verify students' public Google Skills profiles, count unique earned badges, monitor progress against campaign rules and export student-level reports. Instead of requiring campaign coordinators to visit each profile and manually count the badges, the scraper retrieves the profile information, extracts the earned badges, and processes the results.

## ⚙️ How SkillTrack Works

SkillTrack follows a simple six-step workflow:

**1. Upload Student Data**

Upload a CSV file containing student IDs, student names, email addresses, and Google Skills public profile URLs.

**2. Map CSV Columns**

SkillTrack analyses the uploaded file and suggests column mappings. Review and confirm the mapping before proceeding.

**3. Validate the Student List**

The application checks profile URLs, identifies invalid links, and detects duplicate profiles before starting verification.

**4. Verify Google Skills Profiles**

SkillTrack accesses valid public profiles, extracts earned badge information, and calculates the badge count for each student.

**5. Review Results and Track Progress**

View individual student verification results, badge counts, summary statistics, and any errors encountered during processing. Failed verification attempts can be retried.

**6. Generate Reports**

Generate reports containing the collected student verification results for further analysis and record-keeping.

## 🎥 Project Demonstration

Watch SkillTrack v1.2.0 in action:

▶️ **[Watch the SkillTrack Demo Video](https://drive.google.com/drive/folders/1rsVzapTMphU_Ms9hj02M9c4j5xMACMZk?usp=drive_link)**

The demonstration covers the complete workflow, from CSV upload and column mapping to live badge verification, progress tracking, and report generation.

## Highlights
- Campaign Rules: allows coordinators to customise the criteria for campaign completion. For example, if a learning campaign requires students to earn specific Google Skills badges, the coordinator can select the 'Specific Required Badges' verification mode and enter the required badge titles. SkillTrack then compares the badges extracted from each student's profile against these requirements to determine their campaign progress and completion status.
  
- Scraper Settings: provides control over how SkillTrack interacts with the source website. The request delay introduces a pause between profile requests to avoid sending them too rapidly. The maximum retry setting allows temporary failures to be retried, while the timeout prevents the application from waiting indefinitely for an unresponsive profile.
SkillTrack also supports respecting robots.txt instructions. Additionally, a JavaScript rendering fallback is available for websites that load content dynamically.

- Session & Privacy: provides a way to manage the data held during an active SkillTrack session. Uploaded student information and verification results are maintained in the active Streamlit session's server-side memory. Once a verification task is complete, the coordinator can use the Clear Current Session option to clear the loaded student list and results.


## What the application does

- Imports coordinator CSV files up to **5 MB** and detects likely profile URL, student ID, name and email columns.
- Validates Google Skills public-profile URLs, flags malformed links and identifies duplicate profile URLs.
- Checks each unique valid profile sequentially, with configurable delays, timeouts, retries and `robots.txt` checks.
- Counts badge links belonging to the requested profile and de-duplicates by badge title.
- Supports two campaign rules: **any N unique badges** or **specific required badge titles**.
- Supports pending-only checks, retrying failed profiles, re-verifying all profiles, and stopping safely between profile requests.
- Shows searchable student results, profile details, badge titles, campaign statistics, a session-only recent activity log and coordinator reports.
- Lets coordinators retry only previously failed profiles without re-running successful checks.
- Exports Excel-friendly CSV files and protects text fields against spreadsheet formula injection.


## ✨ Key Features

- **CSV Student List Import:** Upload a CSV file containing student details and Google Skills public profile URLs.
- **Smart Column Mapping:** Automatically suggests the appropriate columns based on column names and URL values, with manual confirmation.
- **Profile URL Validation:** Identifies invalid profile links before verification begins.
- **Live Badge Verification:** Fetches public Google Skills profiles and detects earned badges.
- **Duplicate Profile Detection:** Checks identical profile URLs only once and reuses the verification result for matching students.
- **Progress Tracking:** Monitors student badge achievements and provides an overview of verification results.
- **Detailed Error Handling:** Handles invalid URLs, network interruptions, HTTP errors, and failed profile requests with meaningful feedback.
- **Retry Failed Profiles:** Allows unsuccessful verification attempts to be retried.
- **Activity Log:** Provides visibility into verification activity and processing results.
- **Report Generation:** Generates reports from the collected verification results.
- **Modern Dashboard:** A clean interface with a Midnight Teal-inspired colour palette, improved typography, and an intuitive workflow.

## Application workflow

1. **Dashboard:** overview of the process and, after a student list is loaded, campaign metrics and recent results.
2. **Upload Student CSV:** select the URL column and optionally map student ID, name and email. Review invalid and duplicate links before loading the student list.
3. **Verify Profiles:** check pending profiles, retry previously failed profiles, or re-verify the complete valid profile list.
4. **Student Results:** search, filter and inspect individual badge details and verification messages.
5. **Campaign Statistics:** review verification coverage, campaign completion, badge distribution and status counts.
6. **Export Reports:** download the full student report or completed-students-only report.

The sidebar contains a prominent upload action, navigation, campaign-rule settings, scraper settings and session controls. Each page explains its purpose and the information it uses. The interface uses a midnight-teal theme with Manrope/Inter typography and a subtle geometric welcome banner.

## Technology

- Python 3.11+
- Streamlit
- Requests
- BeautifulSoup 4 (uses `lxml` when available and falls back to Python's built-in `html.parser`)
- Pandas and Plotly
- Pytest for automated tests
- Playwright is optional and only used when explicitly enabled

## Project structure

```text
skilltrack/
├── app.py
├── config.py
├── csv_handler.py
├── scraper.py
├── badge_parser.py
├── progress_tracker.py
├── report_generator.py
├── verification.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── README.md
├── .streamlit/
│   └── config.toml
├── assets/
│   └── logo.png
├── sample_data/
│   └── sample_students.csv
├── scripts/
│   └── check_live_reference.py
└── tests/
    ├── fixtures/
    ├── helpers.py
    ├── test_csv_handler.py
    ├── test_parser.py
    ├── test_progress.py
    ├── test_reference_integration.py
    ├── test_scraper.py
    └── test_verification.py
```

## Install and run on Windows

Open PowerShell in the project directory:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
streamlit run app.py
```

If PowerShell blocks virtual-environment activation, use Command Prompt instead:

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
streamlit run app.py
```

The application opens at `http://localhost:8501`.

`lxml` is included in the requirements for faster, consistent HTML parsing. If it is not installed, SkillTrack automatically falls back to `html.parser`; a missing optional parser will no longer crash verification.

## Coordinator CSV format

The only required field is the Google Skills public-profile URL. The recommended columns are:

| Column | Required | Purpose |
|---|---:|---|
| Google Skills Profile URL | Yes | Public profile to verify |
| Student ID | No | Student identifier |
| Student Name | No | Name shown in coordinator reports |
| Email | No | Optional contact field |

Other CSV columns are retained in the full report. The original file is not modified or written to disk by SkillTrack. The configured upload limit is 5 MB.

## Verification methodology

The scraper:

1. Validates the URL host and `/public_profiles/<profile-id>` path.
2. Checks `robots.txt` when that option is enabled.
3. Fetches one profile at a time using the configured request delay.
4. Retries temporary errors such as HTTP 429, HTTP 408/429, selected 5xx responses and network timeouts.
5. Checks that a redirect or canonical page identity still matches the requested profile.
6. Counts links matching `/public_profiles/<profile-id>/badges/<badge-id>` on the student's own profile.
7. De-duplicates earned badges by normalized title.

A page with no badges is treated as zero only when the profile identity can be confirmed. A private profile, an unexpected redirect, an unrecognised layout or a page that cannot be confidently associated with the requested profile is not counted as zero.

### Verification statuses

| Status | Meaning |
|---|---|
| COMPLETED | Verified profile meets the campaign requirement |
| IN PROGRESS | Verified profile has some, but not enough, qualifying badges |
| NOT STARTED | Verified profile currently has zero qualifying badges |
| PENDING | Profile has not yet been checked in this session |
| UNAVAILABLE | Profile is private, missing or access is denied (401/403/404/410) |
| INVALID URL | Supplied URL is not a supported public profile link |
| RATE LIMITED | Google Skills returned HTTP 429; wait and retry |
| NEEDS REVIEW | Profile identity or page layout could not be confirmed safely |
| SCRAPING ERROR | Network, timeout or server failure prevented verification |

Unverified statuses retain a blank badge count. They are never converted into a zero-badge result.

## Campaign rules

- **Any N unique badges:** students meet the requirement after earning the configured number of unique badges. The default is 10.
- **Specific required badges:** students must have every badge title entered in the Campaign rules section. Matching ignores case and repeated whitespace.

The coordinator should confirm which rule applies before verifying the student list.

## Tests and quality checks

Run the deterministic test suite from the project root:

```powershell
python -m pytest -q
```

The automated suite uses local HTML fixtures and mocked HTTP responses, so it does not depend on Google's availability, network access, rate limits or IP reputation. It covers CSV validation and upload limits, parser fallback, badge counting and profile identity, scraper retries and HTTP statuses, progress calculations, exports, and safe stop/resume job behaviour.

For an optional live smoke check against the known public reference profile, run:

```powershell
python scripts/check_live_reference.py
```

The live check requires internet access and may be affected by `robots.txt`, Google Skills availability or rate limiting. It is intentionally separate from the deterministic test suite so a temporary external outage does not create a skipped or flaky automated test.

## Deployment notes

1. Create a private GitHub repository if the source contains any organisation-specific configuration.
2. Push the project files, excluding real coordinator CSVs, environment files and generated reports.
3. Deploy through Streamlit Community Cloud or a university-managed Streamlit host.
4. Restrict access to authorised coordinators before processing real student data.

The included `.gitignore` excludes ordinary CSV files except the fictional sample student list. Review the repository before pushing to ensure no real student data or exported reports are included.

## Privacy and access control

Uploaded student list data and results are held in the active Streamlit session's **server-side memory**. SkillTrack does not persist the uploaded CSV to disk, but the hosting machine processes the data. A public Streamlit URL is **not private**. Use an access-controlled deployment, a university-managed authenticated host or a local run, and follow institutional data-handling requirements. Clear the current session when work is complete.

## Known limitations

- Only public Google Skills profiles can be verified.
- Google may throttle or block automated requests; the application honours configured delays and reports rate-limit responses.
- Google may change its HTML structure. SkillTrack marks unrecognised layouts as NEEDS REVIEW rather than assuming zero badges.
- The badge URL pattern is the basis for counting; the scraper cannot infer badge semantics beyond the public profile links.
- The JavaScript-rendering fallback is optional and requires a separate Playwright and Chromium installation.
