"""SkillTrack — Google Skills Badge Verification Dashboard."""
import html
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
import csv_handler
import progress_tracker
import report_generator
from verification import VerificationJob

ROOT = Path(__file__).parent
PAGES = [
    "Dashboard",
    "Upload Student CSV",
    "Verify Profiles",
    "Student Results",
    "Campaign Statistics",
    "Export Reports",
    "About / Help",
]

st.set_page_config(
    page_title=f"{config.APP_NAME} | {config.CAMPAIGN_NAME}",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root {
  --ink: #142A36;
  --teal: #1C8C83;
  --teal-dark: #176D68;
  --mint: #DFF3EF;
  --ivory: #F6F7F3;
  --amber: #E5A44D;
  --muted: #6C7D82;
  --line: #E1E9E6;
}
#MainMenu, footer, .stDeployButton {visibility:hidden;}
html, body, [class*="css"] {font-family:'Inter',sans-serif;}
h1, h2, h3, h4, [data-testid="stMetricValue"] {font-family:'Manrope','Inter',sans-serif;}
.block-container {padding-top:1.4rem; padding-bottom:3rem; max-width:1480px;}
[data-testid="stAppViewContainer"] {background:var(--ivory);}
[data-testid="stMainBlockContainer"] {padding-left:2.4rem; padding-right:2.4rem;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#142A36 0%,#193C45 100%); border-right:1px solid rgba(255,255,255,.06);}
[data-testid="stSidebar"] * {color:#F1F7F5;}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-baseweb="input"] input {color:#142A36 !important;}
[data-testid="stSidebar"] [role="radiogroup"] label {padding:.5rem .72rem; border-radius:10px; margin-bottom:3px;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:rgba(255,255,255,.09);}
[data-testid="stSidebar"] [data-testid="stExpander"] {border-color:rgba(255,255,255,.16); border-radius:12px;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {font-weight:600;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#B9CBCB;}
.brand {display:flex; align-items:center; gap:.7rem; margin:.25rem 0 1rem 0;}
.brand b {font-family:'Manrope',sans-serif; font-size:1.42rem; color:#fff; letter-spacing:-.035em;}
.brand small {color:#B7DCD5; display:block; margin-top:-3px; font-size:.76rem;}
.nav-label {font-size:.7rem; letter-spacing:.14em; font-weight:700; color:#9BBDB8; margin:.7rem 0 .45rem .15rem;}
.hero {position:relative; overflow:hidden; isolation:isolate; background:
       radial-gradient(circle at 84% 18%,rgba(191,242,230,.22) 0,transparent 30%),
       radial-gradient(circle at 100% 100%,rgba(229,164,77,.17) 0,transparent 34%),
       linear-gradient(115deg,#142A36 0%,#176D68 72%,#1C8C83 100%);
       color:#fff; padding:1.7rem 1.9rem; border-radius:20px;
       box-shadow:0 14px 32px rgba(20,42,54,.13); margin-bottom:1.25rem;}
.hero:after {content:""; position:absolute; inset:0; z-index:0; pointer-events:none; opacity:.22;
             background-image:radial-gradient(circle at 1px 1px,rgba(255,255,255,.78) 1px,transparent 1.5px);
             background-size:23px 23px; mask-image:linear-gradient(110deg,transparent 10%,#000 100%);}
.hero > * {position:relative; z-index:1;}
.hero .eyebrow {font-size:.7rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase; color:#C9EAE3; margin-bottom:.42rem;}
.hero h1 {margin:0; font-family:'Manrope',sans-serif; font-size:1.95rem; line-height:1.2; color:#fff; letter-spacing:-.035em;}
.hero p {margin:.5rem 0 0; color:#EAF7F4; opacity:.96; font-size:.98rem; max-width:900px; line-height:1.6;}
.section-kicker {font-size:.7rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; color:var(--teal-dark);}
.info-card {background:#fff; border:1px solid var(--line); border-radius:16px; padding:1.15rem 1.25rem; height:100%; box-shadow:0 4px 18px rgba(20,42,54,.035); transition:transform .16s ease,box-shadow .16s ease;}
.info-card:hover {transform:translateY(-2px); box-shadow:0 8px 22px rgba(20,42,54,.08);}
.info-card h3 {margin:.15rem 0 .4rem; color:var(--ink); font-family:'Manrope',sans-serif; font-size:1.03rem;}
.info-card p {margin:0; color:var(--muted); font-size:.88rem; line-height:1.6;}
.step-number {display:inline-flex; width:2rem; height:2rem; border-radius:10px; align-items:center; justify-content:center;
              background:var(--mint); color:var(--teal-dark); font-weight:800; margin-bottom:.6rem;}
.kpi {background:#fff; border:1px solid var(--line); border-radius:15px; padding:1rem 1.1rem; box-shadow:0 4px 16px rgba(20,42,54,.035); height:100%;}
.kpi-l {font-size:.72rem; text-transform:uppercase; letter-spacing:.065em; color:var(--muted); font-weight:800;}
.kpi-v {font-family:'Manrope',sans-serif; font-size:1.95rem; font-weight:800; color:var(--ink); line-height:1.25; margin:.28rem 0;}
.kpi-s {font-size:.76rem; color:var(--muted); min-height:1rem; line-height:1.45;}
.pill {display:inline-block; padding:.2rem .68rem; border-radius:999px; color:#fff; font-weight:700; font-size:.7rem; letter-spacing:.015em; white-space:nowrap;}
.muted {color:var(--muted);}
.small-note {font-size:.82rem; color:var(--muted);}
[data-testid="stMetric"] {background:#fff; border:1px solid var(--line); border-radius:14px; padding:.82rem 1rem; box-shadow:0 3px 12px rgba(20,42,54,.025);}
[data-testid="stMetricLabel"] {color:var(--muted); font-weight:600;}
[data-testid="stMetricValue"] {color:var(--ink);}
[data-testid="stDataFrame"], [data-testid="stTable"] {border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff;}
[data-testid="stExpander"] {border:1px solid var(--line); border-radius:13px; background:rgba(255,255,255,.72);}
button[kind="primary"] {background:#1C8C83; border-color:#1C8C83; color:#fff; box-shadow:0 5px 14px rgba(28,140,131,.16);}
button[kind="primary"]:hover {background:#176D68; border-color:#176D68;}
[data-testid="stDownloadButton"] button {border-radius:10px;}
[data-testid="stFileUploader"] section {background:#fff; border:1px dashed #B7CBC5; border-radius:14px;}
hr {border-color:var(--line);}
@media (max-width: 800px) {
  [data-testid="stMainBlockContainer"] {padding-left:1rem; padding-right:1rem;}
  .hero {padding:1.3rem 1.25rem;}
  .hero h1 {font-size:1.55rem;}
}
</style>
"""


# ---------------------------------------------------------------- state helpers
def init_state():
    ss = st.session_state
    ss.setdefault("page", "Dashboard")
    ss.setdefault("students", None)
    ss.setdefault("raw", {})
    ss.setdefault("csv_name", "")
    ss.setdefault("pending_students", None)
    ss.setdefault("pending_csv_name", "")
    ss.setdefault("verification_job", None)
    ss.setdefault("last_verification_summary", None)
    ss.setdefault("confirm_reset", False)
    ss.setdefault("activity_log", [])
    ss.setdefault("activity_seen", set())


def set_page(page):
    st.session_state.page = page


def reset_session():
    """Clear uploaded data and verification results after explicit confirmation."""
    ss = st.session_state
    ss.students = None
    ss.raw = {}
    ss.csv_name = ""
    ss.pending_students = None
    ss.pending_csv_name = ""
    ss.verification_job = None
    ss.last_verification_summary = None
    ss.activity_log = []
    ss.activity_seen = set()
    ss.confirm_reset = False
    ss.page = "Dashboard"


def commit_pending_students():
    ss = st.session_state
    ss.students = ss.pending_students
    ss.raw = {}
    ss.csv_name = ss.pending_csv_name
    ss.pending_students = None
    ss.last_verification_summary = None
    ss.page = "Verify Profiles"


def dismiss_last_summary():
    st.session_state.last_verification_summary = None


def settings():
    ss = st.session_state
    return {
        "mode": ss.get("cfg_mode", config.MODE_COUNT),
        "required": int(ss.get("cfg_required", config.REQUIRED_BADGES)),
        "titles": progress_tracker.parse_required_titles(ss.get("cfg_titles", "")),
        "delay": float(ss.get("cfg_delay", config.REQUEST_DELAY)),
        "retries": int(ss.get("cfg_retries", config.MAX_RETRIES)),
        "timeout": int(ss.get("cfg_timeout", config.REQUEST_TIMEOUT)),
        "robots": bool(ss.get("cfg_robots", config.CHECK_ROBOTS)),
        "playwright": bool(ss.get("cfg_playwright", False)),
    }


def get_results():
    ss = st.session_state
    if ss.students is None:
        return None
    cfg = settings()
    return progress_tracker.build_results_df(
        ss.students, ss.raw, cfg["required"], cfg["mode"], cfg["titles"]
    )


def pill(status):
    color = config.STATUS_COLORS.get(status, "#64748b")
    return f'<span class="pill" style="background:{color}">{html.escape(str(status))}</span>'


def kpi(label, value, color, sub=""):
    return (
        f'<div class="kpi" style="border-top:4px solid {color}">'
        f'<div class="kpi-l">{html.escape(str(label))}</div>'
        f'<div class="kpi-v">{html.escape(str(value))}</div>'
        f'<div class="kpi-s">{html.escape(str(sub))}</div></div>'
    )


def style_table(df):
    def color(value):
        c = config.STATUS_COLORS.get(value)
        return f"background-color:{c}; color:white; font-weight:700" if c else ""

    styler = df.style
    return (styler.map if hasattr(styler, "map") else styler.applymap)(color, subset=["Status"])


def hero(title, description, eyebrow="LEARN WITH COMMUNITIES"):
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{html.escape(eyebrow)}</div>'
        f'<h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></div>',
        unsafe_allow_html=True,
    )


def need_students():
    if st.session_state.students is None:
        st.info("There is no student list in this session yet. Upload the coordinator CSV to get started.")
        st.button(
            "Upload student CSV",
            type="primary",
            on_click=set_page,
            args=("Upload Student CSV",),
        )
        return True
    return False


def status_guide():
    with st.expander("Understand verification statuses"):
        for status, description in config.STATUS_DESCRIPTIONS.items():
            st.markdown(f"{pill(status)} &nbsp; {html.escape(description)}", unsafe_allow_html=True)


# ---------------------------------------------------------------- sidebar
def sidebar():
    with st.sidebar:
        logo = ROOT / "assets" / "logo.png"
        c1, c2 = st.columns([1, 3])
        if logo.exists():
            c1.image(str(logo), width=48)
        c2.markdown(
            f'<div class="brand"><div><b>{html.escape(config.APP_NAME)}</b>'
            f'<small>{html.escape(config.CAMPAIGN_NAME)}</small></div></div>',
            unsafe_allow_html=True,
        )

        st.button(
            "＋  Upload student CSV",
            key="sidebar_upload_action",
            type="primary",
            use_container_width=True,
            on_click=set_page,
            args=("Upload Student CSV",),
        )
        st.markdown('<div class="nav-label">WORKSPACE</div>', unsafe_allow_html=True)
        st.radio("Navigation", PAGES, key="page", label_visibility="collapsed")

        if st.session_state.students is not None:
            count = len(st.session_state.students)
            verified = sum(
                1 for result in st.session_state.raw.values()
                if result.get("status") == config.SUCCESS
            )
            st.caption(f"{count} student rows loaded · {verified} unique profiles verified")

        st.markdown("---")
        with st.expander("Campaign rules", expanded=False):
            st.caption("Choose how SkillTrack decides whether a student has completed the campaign.")
            selected_mode = st.selectbox(
                "Verification mode",
                [config.MODE_COUNT, config.MODE_REQUIRED],
                key="cfg_mode",
                format_func=lambda mode: "Any N unique badges" if mode == config.MODE_COUNT else "Specific required badges",
                help="Count mode accepts any unique earned badges. Specific mode checks the exact titles listed below.",
            )
            if selected_mode == config.MODE_COUNT:
                st.number_input(
                    "Required unique badges", 1, 100, config.REQUIRED_BADGES,
                    key="cfg_required", help="The number of unique earned badges required for completion.",
                )
            else:
                st.text_area(
                    "Required badge titles (one per line)", key="cfg_titles", height=120,
                    help="Enter the exact campaign badge titles, one per line. Matching ignores case and repeated whitespace.",
                )

        with st.expander("Scraper settings", expanded=False):
            st.caption("These controls help keep requests sequential and respectful of the source website.")
            st.number_input(
                "Delay between requests (seconds)", 0.5, 30.0, config.REQUEST_DELAY, 0.25,
                key="cfg_delay", help="Wait time between profile requests. Increase this if Google Skills rate-limits the session.",
            )
            st.number_input(
                "Maximum retries", 0, 6, config.MAX_RETRIES, key="cfg_retries",
                help="How many times temporary network, timeout, 429 or server errors are retried.",
            )
            st.number_input(
                "Request timeout (seconds)", 5, 120, config.REQUEST_TIMEOUT, key="cfg_timeout",
                help="Maximum wait for one HTTP request before it is treated as a timeout.",
            )
            st.checkbox(
                "Respect robots.txt", config.CHECK_ROBOTS, key="cfg_robots",
                help="Do not scrape profile pages when the website's robots.txt disallows it.",
            )
            st.checkbox(
                "Use JavaScript rendering fallback", False, key="cfg_playwright",
                help="Optional Playwright fallback for pages that do not expose badge links in their initial HTML. Requires Playwright and Chromium to be installed.",
            )

        with st.expander("Session and privacy", expanded=False):
            st.caption("Uploaded student data and verification results are held in the active Streamlit session's server-side memory.")
            running_job = st.session_state.verification_job
            is_running = bool(running_job and running_job.snapshot()["running"])
            if is_running:
                st.warning("A verification run is active. Stop or finish it before clearing this session.")
            confirm = st.checkbox(
                "I understand this clears the loaded student list and results.",
                key="confirm_reset",
            )
            st.button(
                "Clear current session",
                use_container_width=True,
                disabled=not confirm or is_running,
                on_click=reset_session,
            )


# ---------------------------------------------------------------- dashboard
def page_dashboard():
    hero("Student badge verification, made manageable", "Upload a student list, verify public Google Skills profiles, and track campaign completion from one workspace.")
    results = get_results()

    if results is None:
        left, right = st.columns([1.35, 1], gap="large")
        with left:
            with st.container(border=True):
                st.markdown('<div class="section-kicker">GET STARTED</div>', unsafe_allow_html=True)
                st.markdown("### Start a verification run")
                st.write("Start with the student list supplied by the campaign coordinator. SkillTrack helps map profile links, check each public profile and prepare a results report.")
                st.button(
                    "Upload coordinator CSV  →",
                    type="primary",
                    use_container_width=True,
                    on_click=set_page,
                    args=("Upload Student CSV",),
                )
                st.caption("CSV format · up to 5 MB · Google Skills profile URL required")
        with right:
            with st.container(border=True):
                st.markdown('<div class="section-kicker">WHAT SKILLTRACK CHECKS</div>', unsafe_allow_html=True)
                st.markdown("### A consistent verification process")
                st.markdown("- **Profile links:** validates each public profile URL before making a request.")
                st.markdown("- **Earned badges:** counts unique badge links on the student's own profile.")
                st.markdown("- **Campaign rules:** compares verified badges against the selected requirement.")
                st.markdown("- **Review and export:** highlights profiles that need attention and prepares coordinator reports.")
        st.markdown("### Three steps from student list to report")
        steps = st.columns(3, gap="medium")
        step_data = [
            ("01", "Upload the student list", "Add the coordinator CSV and confirm which columns contain profile URLs and student details."),
            ("02", "Verify public profiles", "SkillTrack checks profiles one at a time, records earned badges and preserves partial progress."),
            ("03", "Review and export", "Filter student results, inspect badge details, view campaign coverage and download reports."),
        ]
        for col, (number, title, description) in zip(steps, step_data):
            with col:
                st.markdown(
                    f'<div class="info-card"><div class="step-number">{number}</div>'
                    f'<h3>{title}</h3><p>{description}</p></div>',
                    unsafe_allow_html=True,
                )
        st.info("Privacy note: uploaded data is held in the active Streamlit session's server-side memory. A publicly shared Streamlit URL is not private; use access controls before uploading real student information.")
        return

    summary = progress_tracker.summarize(results)
    st.markdown("<div class='section-kicker'>CAMPAIGN OVERVIEW</div>", unsafe_allow_html=True)
    cards = [
        ("Students in list", summary["total"], "#142A36", st.session_state.csv_name or "Current session"),
        ("Student rows verified", summary["verified"], "#1C8C83", f'{summary["verification_rate_pct"]:.1f}% verification coverage'),
        ("Campaign completed", summary["completed"], "#16866f", f'{summary["completion_rate_pct"]:.1f}% of students'),
        ("Needs attention", summary["unverified"], "#C45F59", "Could not be confidently verified"),
    ]
    cols = st.columns(4, gap="medium")
    for col, item in zip(cols, cards):
        col.markdown(kpi(*item), unsafe_allow_html=True)

    st.markdown("### Campaign progress")
    st.progress(summary["completion_rate_pct"] / 100)
    st.caption(f'{summary["completed"]} of {summary["total"]} students currently meet the selected campaign requirement. Verification coverage is {summary["verified"]} of {summary["total"]}.')

    a, b, c = st.columns(3)
    a.button("Continue verification", use_container_width=True, on_click=set_page, args=("Verify Profiles",))
    b.button("View student results", use_container_width=True, on_click=set_page, args=("Student Results",))
    c.button("Export reports", use_container_width=True, on_click=set_page, args=("Export Reports",))

    st.markdown("### Latest student results")
    visible = results[["Student ID", "Student Name", "Earned Badges", "Required", "Progress", "Status"]].head(10)
    st.dataframe(
        style_table(visible), hide_index=True, use_container_width=True,
        column_config={
            "Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%.0f%%"),
            "Earned Badges": st.column_config.NumberColumn("Earned badges", format="%d"),
        },
    )
    if st.session_state.activity_log:
        st.markdown("### Recent verification activity")
        activity = pd.DataFrame(st.session_state.activity_log[:8])
        st.dataframe(
            activity[["Time", "Student", "Student ID", "Status", "Message"]],
            hide_index=True, use_container_width=True,
            column_config={"Message": st.column_config.TextColumn("Result", width="large")},
        )
    status_guide()


# ---------------------------------------------------------------- upload
def page_upload():
    hero("Upload student CSV", "Add the coordinator's student list and confirm the columns SkillTrack should use.", "STEP 1 · STUDENT LIST")
    st.markdown("A Google Skills public-profile URL is required for every student. Student ID, name and email are optional, but recommended for clearer reports.")
    st.caption("A student list is simply the CSV file containing the students you want to check.")
    st.info("Accepted file: CSV · Maximum size: 5 MB · The original file is not modified or written to disk by SkillTrack.")

    upload = st.file_uploader(
        "Choose coordinator CSV",
        type=["csv"],
        key="student_csv_uploader",
        help="Upload the coordinator's student CSV. The file must include a column containing Google Skills public-profile URLs.",
    )
    if not upload:
        with st.container(border=True):
            st.markdown("**Required column**")
            st.code("Google Skills Profile URL", language="text")
            st.markdown("**Optional columns**")
            st.write("Student ID · Student Name · Email")
            st.caption("Column names are detected automatically where possible. You can correct the mapping after selecting a file.")
        return

    try:
        payload = upload.getvalue()
    except Exception as exc:
        st.error("SkillTrack could not access the uploaded file. Please select it again.")
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {exc}")
        return
    if len(payload) > config.MAX_UPLOAD_BYTES:
        st.error("This file is larger than the 5 MB upload limit. Split the student list into smaller CSV files and upload them separately.")
        return

    st.session_state.pending_students = None
    try:
        dataframe = csv_handler.load_csv(payload)
    except csv_handler.CSVError as exc:
        st.error(str(exc))
        with st.expander("How to fix this file"):
            st.markdown(
                "- Make sure the first row contains column headings.\n"
                "- Check that each row has the same number of columns.\n"
                "- Save or export the file as **CSV UTF-8**.\n"
                "- Confirm that the file is not empty and is smaller than 5 MB."
            )
        return
    except Exception as exc:
        st.error("SkillTrack could not read this upload. Please check the CSV and try again.")
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {exc}")
        return

    if dataframe.attrs.get("empty_rows_dropped"):
        st.caption(f'{dataframe.attrs["empty_rows_dropped"]} completely empty row(s) will be ignored.')

    detected = csv_handler.detect_columns(dataframe)
    st.markdown("### Confirm column mapping")
    st.caption("SkillTrack suggests a mapping based on column names and URL values. Check it before loading the student list.")
    options = ["(none)"] + list(dataframe.columns)
    columns = st.columns(4, gap="medium")
    mapping = {}
    for column, (key, label) in zip(columns, [
        ("url", "Profile URL · required"),
        ("id", "Student ID"),
        ("name", "Student Name"),
        ("email", "Email"),
    ]):
        default = options.index(detected[key]) if detected.get(key) in options else 0
        choice = column.selectbox(
            label, options, index=default, key=f"map_{key}_{upload.name}",
            help="Choose the CSV column that contains this information, or select (none) if it is not present.",
        )
        mapping[key] = None if choice == "(none)" else choice

    try:
        students = csv_handler.build_students(dataframe, mapping)
    except csv_handler.CSVError as exc:
        st.error(str(exc))
        st.caption("Select the column containing Google Skills public-profile URLs, or correct the column mapping above.")
        return
    except Exception as exc:
        st.error("SkillTrack could not prepare the student list. Please review the column mapping and try again.")
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {exc}")
        return

    st.session_state.pending_students = students
    st.session_state.pending_csv_name = upload.name
    issues = csv_handler.summarize_issues(students)
    metrics = st.columns(4)
    metrics[0].metric("Student rows", issues["rows"])
    metrics[1].metric("Valid profile URLs", issues["valid"])
    metrics[2].metric("Invalid URLs", issues["invalid"])
    metrics[3].metric("Duplicate profiles", issues["duplicates"])

    if issues["invalid"]:
        st.warning("Invalid profile links will be marked INVALID URL. They will not be treated as students with zero badges.")
    if issues["duplicates"]:
        st.info("Duplicate profile URLs are checked once. The same verification result is reused for each matching student row.")

    st.markdown("### Review student list")
    st.dataframe(
        students[["Row", "Student ID", "Student Name", "Profile URL", "URL Valid", "URL Error", "Duplicate Profile"]],
        hide_index=True,
        use_container_width=True,
    )
    st.button(
        "Load student list and continue  →",
        type="primary",
        on_click=commit_pending_students,
        help="Loads the validated student list into this session and opens the verification step.",
    )


# ---------------------------------------------------------------- verification
@st.fragment(run_every="1s")
def render_verification_monitor():
    job = st.session_state.get("verification_job")
    if job is None:
        return
    snapshot = job.snapshot()
    # Copy completed profile results into session state on the UI thread and record
    # a compact, session-only activity history. The worker itself never mutates UI state.
    for url, result in snapshot["results"].items():
        checked_at = result.get("checked_at") or ""
        event_key = f"{id(job)}|{url}|{checked_at}"
        if checked_at and event_key not in st.session_state.activity_seen:
            matching = st.session_state.students[st.session_state.students["Profile URL"] == url]
            first = matching.iloc[0] if not matching.empty else None
            cfg = settings()
            evaluation = progress_tracker.evaluate(result, cfg["required"], cfg["mode"], cfg["titles"])
            st.session_state.activity_log.insert(0, {
                "Time": checked_at,
                "Student": ((first["Student Name"] if first is not None else "") or result.get("profile_name") or "Name not provided"),
                "Student ID": (first["Student ID"] if first is not None else "") or "—",
                "Status": evaluation["status"],
                "Message": result.get("error") or "Profile checked successfully.",
                "Profile URL": url,
            })
            st.session_state.activity_seen.add(event_key)
    st.session_state.activity_log = st.session_state.activity_log[:50]
    st.session_state.raw.update(snapshot["results"])
    total = snapshot["total"]
    processed = snapshot["processed"]
    fraction = processed / total if total else 1.0
    st.markdown("### Verification progress")
    st.progress(fraction)
    a, b, c = st.columns(3)
    a.metric("Profiles processed", f"{processed} / {total}")
    b.metric("Successful", snapshot["successful"])
    c.metric("Needs attention", snapshot["failed"])

    if snapshot["running"]:
        st.info("Profiles are being checked sequentially. You can stop safely after the current profile request finishes.")
        st.button(
            "Stop after current profile",
            key="stop_verification_job",
            on_click=job.request_stop,
            help="Keeps all results already collected and stops before starting the next profile.",
        )
    else:
        st.session_state.last_verification_summary = snapshot
        if snapshot["error"]:
            st.error(snapshot["error"])
            if snapshot.get("technical_error"):
                with st.expander("Technical details (for troubleshooting)"):
                    st.code(snapshot["technical_error"])
        elif snapshot["stopped"]:
            st.warning(f"Verification paused after {processed} of {total} profiles. Results already collected have been saved. Choose Pending profiles to continue.")
        else:
            st.success(f"Verification finished. {snapshot['successful']} profiles were read successfully; {snapshot['failed']} need attention.")
        if st.button("Return to verification controls", key="close_verification_summary"):
            st.session_state.verification_job = None
            st.rerun()


def page_verify():
    hero("Verify Google Skills profiles", "Check each valid public profile once, record its earned badges, and preserve results if you pause the run.", "STEP 2 · PROFILE VERIFICATION")
    if need_students():
        return

    ss = st.session_state
    job = ss.verification_job
    if job is not None:
        render_verification_monitor()
        return

    if ss.last_verification_summary:
        previous = ss.last_verification_summary
        if previous["stopped"]:
            st.warning(f'Last run paused at {previous["processed"]} of {previous["total"]} profiles. Completed results are retained.')
        else:
            st.success(f'Last run processed {previous["processed"]} profile(s): {previous["successful"]} successful and {previous["failed"]} needing attention.')
        st.button("Dismiss previous run summary", on_click=dismiss_last_summary)

    cfg = settings()
    students = ss.students
    valid_urls = list(dict.fromkeys(students.loc[students["URL Valid"], "Profile URL"].tolist()))
    verified_count = sum(1 for url in valid_urls if ss.raw.get(url, {}).get("status") == config.SUCCESS)
    pending_count = sum(1 for url in valid_urls if url not in ss.raw)
    retry_count = sum(
        1 for url in valid_urls
        if url in ss.raw and ss.raw.get(url, {}).get("status") in config.RETRYABLE_STATUSES
    )

    metrics = st.columns(4)
    metrics[0].metric("Student rows", len(students))
    metrics[1].metric("Unique valid profiles", len(valid_urls))
    metrics[2].metric("Verified successfully", verified_count)
    metrics[3].metric("Failed checks", retry_count)

    st.markdown("### Choose what to verify")
    st.caption("Successful checks are kept. You can run profiles that have not been checked, retry previous failures, or deliberately verify every profile again.")
    rule_ready = cfg["mode"] != config.MODE_REQUIRED or bool(cfg["titles"])
    if not rule_ready:
        st.warning("Specific required badges mode is selected, but no badge titles are configured. Add the campaign titles in the sidebar before starting verification, or switch to Any N unique badges.")

    scope = st.radio(
        "Verification scope",
        ["Pending profiles", "Retry failed profiles", "Re-verify all profiles"],
        horizontal=True,
        key="verify_scope",
        help="Pending checks profiles not yet attempted. Retry failed checks only re-runs profiles with a previous retryable failure. Re-verify all fetches every valid unique profile again.",
    )
    if scope == "Pending profiles":
        todo = [url for url in valid_urls if url not in ss.raw]
    elif scope == "Retry failed profiles":
        todo = [
            url for url in valid_urls
            if url in ss.raw and ss.raw.get(url, {}).get("status") in config.RETRYABLE_STATUSES
        ]
    else:
        todo = valid_urls

    estimated_seconds = len(todo) * (cfg["delay"] + min(cfg["timeout"], 8))
    with st.container(border=True):
        left, right = st.columns([1.5, 1])
        with left:
            st.markdown(f"**{len(todo)} profile(s) selected**")
            st.write("The estimate is approximate; actual time depends on response speed, retries and rate limiting.")
            st.caption(f"Approximate run time: about {estimated_seconds / 60:.1f} minutes. Actual time varies with network response and retries.")
        with right:
            st.metric("Valid profiles remaining in this selection", len(todo))

    # Start the worker only after the coordinator explicitly confirms this selection.
    if not valid_urls:
        st.warning("No valid Google Skills public-profile URLs were found in this student list. Correct the URL column and upload the student list again before verifying.")
        st.button("Upload corrected student list", on_click=set_page, args=("Upload Student CSV",))
    elif not todo:
        st.success("There are no profiles in this selection. Choose another verification scope if you need to run more checks.")
    if todo and st.button("Verify selected profiles  →", type="primary", use_container_width=True, disabled=not rule_ready, key="verify_selected_profiles"):
        options = {
            "delay": cfg["delay"],
            "timeout": cfg["timeout"],
            "max_retries": cfg["retries"],
            "use_playwright": cfg["playwright"],
            "check_robots": cfg["robots"],
        }
        new_job = VerificationJob(todo, scraper_options=options)
        ss.verification_job = new_job
        ss.last_verification_summary = None
        try:
            new_job.start()
        except Exception as exc:
            ss.verification_job = None
            st.error("SkillTrack could not start the verification run. Please try again.")
            with st.expander("Technical details"):
                st.code(f"{type(exc).__name__}: {exc}")
            return
        st.rerun()

    with st.expander("What happens during verification?", expanded=False):
        st.markdown(
            "1. Validate the URL and confirm it belongs to an allowed Google Skills host.\n"
            "2. Check robots.txt when enabled, then fetch profiles sequentially with the configured delay.\n"
            "3. Retry temporary failures within the configured limit.\n"
            "4. Count unique badge links on the student's own profile; never infer zero badges from an unrecognised page.\n"
            "5. Save each completed result immediately so a paused run can be resumed."
        )
    status_guide()


# ---------------------------------------------------------------- results
def page_results():
    hero("Student results", "Search the student list, compare badge progress, and inspect the badges detected on each profile.", "STEP 3 · RESULTS REVIEW")
    results = get_results()
    if results is None:
        need_students()
        return

    c1, c2, c3 = st.columns([2, 2, 1])
    query = c1.text_input("Search by student name or ID", help="Searches the coordinator-provided student name and student ID.")
    statuses = c2.multiselect("Filter by status", sorted(results["Status"].unique()))
    quick = c3.selectbox("Quick filter", ["All students", "Completed", "Incomplete", "Needs attention"])
    sort = st.radio("Sort by earned badges", ["As uploaded", "High → low", "Low → high"], horizontal=True)

    view = results
    if query:
        mask = view["Student Name"].str.contains(query, case=False, na=False) | view["Student ID"].str.contains(query, case=False, na=False)
        view = view[mask]
    if statuses:
        view = view[view["Status"].isin(statuses)]
    if quick == "Completed":
        view = view[view["Status"] == config.COMPLETED]
    elif quick == "Incomplete":
        view = view[view["Status"].isin([config.IN_PROGRESS, config.NOT_STARTED])]
    elif quick == "Needs attention":
        view = view[view["Status"].isin(config.UNVERIFIED_STATUSES)]
    if sort != "As uploaded":
        view = view.sort_values("Earned Badges", ascending=(sort == "Low → high"), na_position="last")

    columns = ["Student ID", "Student Name", "Profile URL", "Earned Badges", "Required", "Progress", "Status"]
    st.dataframe(
        style_table(view[columns]), hide_index=True, use_container_width=True,
        column_config={
            "Profile URL": st.column_config.LinkColumn("Google Skills profile", display_text="Open profile"),
            "Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%.0f%%"),
            "Earned Badges": st.column_config.NumberColumn("Earned badges", format="%d"),
        },
    )
    st.caption(f'{len(view)} of {len(results)} student rows shown. A blank badge count means verification was not conclusive; it does not mean zero badges.')
    status_guide()

    st.markdown("### Student details")
    if results.empty:
        return
    labels = {
        idx: f'{row["Student ID"] or "No ID"} · {row["Student Name"] or "Name not provided"} · row {row["Row"]}'
        for idx, row in results.iterrows()
    }
    selected = st.selectbox("Select a student", list(labels), format_func=labels.get)
    row = results.loc[selected]
    raw = st.session_state.raw.get(row["Profile URL"], {})
    display_name = row["Student Name"] or row["Google Skills Name"] or "Name not provided"
    with st.container(border=True):
        st.markdown(
            f'<h3 style="margin:0">{html.escape(display_name)} &nbsp; {pill(row["Status"])}</h3>'
            f'<p class="muted" style="margin:.35rem 0 0">Student ID: {html.escape(row["Student ID"] or "—")}</p>',
            unsafe_allow_html=True,
        )
        st.caption(config.STATUS_DESCRIPTIONS.get(row["Status"], "Status information is not available."))

    metrics = st.columns(4)
    metrics[0].metric("Earned badges", "—" if pd.isna(row["Earned Badges"]) else int(row["Earned Badges"]))
    metrics[1].metric("Required", "—" if pd.isna(row["Required"]) else int(row["Required"]))
    metrics[2].metric("Completion", "—" if pd.isna(row["Progress"]) else f'{row["Progress"]:.0f}%')
    checked_at = row["Last Checked"] or ""
    metrics[3].metric("Last checked", checked_at.split(" ")[0] if checked_at else "Not checked")
    if checked_at:
        st.caption(f"Full verification timestamp: {checked_at}")

    if row["Profile URL"]:
        st.markdown(f'[Open Google Skills profile]({row["Profile URL"]})')
    if row["Google Skills Name"] and row["Google Skills Name"] != row["Student Name"]:
        st.caption(f'Name shown on Google Skills: {row["Google Skills Name"]}')
    if row["Error Message"]:
        st.warning(row["Error Message"])
    if raw.get("technical_error"):
        with st.expander("Technical details (for troubleshooting)"):
            st.code(raw["technical_error"])
    if raw.get("badges"):
        badges = pd.DataFrame(raw["badges"]).rename(columns={
            "title": "Badge", "earned_date": "Earned date (ISO)", "earned_text": "Earned date (as shown)"
        })
        st.markdown(f'**{len(badges)} unique earned badges detected**')
        st.dataframe(badges[["Badge", "Earned date (ISO)", "Earned date (as shown)"]], hide_index=True, use_container_width=True)
    elif raw.get("status") == config.SUCCESS:
        st.info("The profile was read successfully and currently shows no earned badges.")


# ---------------------------------------------------------------- statistics
def page_stats():
    hero("Campaign statistics", "Understand verification coverage, completion progress and the students who need follow-up.", "CAMPAIGN ANALYTICS")
    results = get_results()
    if results is None:
        need_students()
        return

    summary = progress_tracker.summarize(results)
    incomplete = summary["in_progress"] + summary["not_started"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verification coverage", f'{summary["verification_rate_pct"]:.1f}%', f'{summary["verified"]} / {summary["total"]} students')
    c2.metric("Campaign completion", f'{summary["completion_rate_pct"]:.1f}%', f'{summary["completed"]} completed')
    c3.metric("Needs attention", summary["unverified"], "Private, invalid or inconclusive")
    c4.metric("Pending checks", summary["pending"], "Not yet attempted")
    st.caption("Verification coverage counts student rows whose linked profiles were read successfully. Campaign completion counts only students who meet the selected badge requirement.")

    left, right = st.columns(2, gap="large")
    donut = go.Figure(go.Pie(
        labels=["Completed", "Incomplete", "Could not verify", "Pending"],
        values=[summary["completed"], incomplete, summary["unverified"], summary["pending"]],
        hole=.62,
        marker_colors=["#1C8C83", "#E5A44D", "#C45F59", "#9AA9A8"],
        textinfo="label+value",
    ))
    donut.update_layout(title="Student campaign status", margin=dict(t=55, b=15, l=10, r=10), legend_title_text="")
    left.plotly_chart(donut, use_container_width=True)

    gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=summary["completion_rate_pct"], number={"suffix": "%"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#1C8C83"}, "steps": [
            {"range": [0, 50], "color": "#EAF4F1"}, {"range": [50, 100], "color": "#DFF3EF"}
        ]},
        title={"text": "Campaign completion across the student list"},
    ))
    gauge.update_layout(margin=dict(t=75, b=20, l=25, r=25))
    right.plotly_chart(gauge, use_container_width=True)

    left, right = st.columns(2, gap="large")
    verified_rows = results[results["Earned Badges"].notna()]
    if verified_rows.empty:
        left.info("Badge distribution will appear after at least one profile is verified.")
    else:
        distribution = verified_rows["Earned Badges"].astype(int).value_counts().sort_index().rename_axis("Badges").reset_index(name="Students")
        left.plotly_chart(
            px.bar(distribution, x="Badges", y="Students", title="Distribution of earned badges", color_discrete_sequence=["#1C8C83"]),
            use_container_width=True,
        )
    status_counts = results["Status"].value_counts().rename_axis("Status").reset_index(name="Students")
    right.plotly_chart(
        px.bar(status_counts, x="Status", y="Students", color="Status", title="Students by verification status", color_discrete_map=config.STATUS_COLORS),
        use_container_width=True,
    )
    status_guide()


# ---------------------------------------------------------------- exports
def page_export():
    hero("Export coordinator reports", "Download a complete student-level report or a separate list of students who have completed the campaign.", "REPORTING")
    results = get_results()
    if results is None:
        need_students()
        return

    summary = progress_tracker.summarize(results)
    st.markdown("Reports are generated from the current session's verification results. CSV files use UTF-8 with BOM for spreadsheet compatibility, and text values are protected against formula injection.")
    if summary["pending"]:
        st.warning(f'{summary["pending"]} student(s) have not been checked yet. They remain in the full report with PENDING status.')

    full_report = report_generator.build_report(results)
    completed_report = report_generator.build_report(results, completed_only=True)
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### Full verification report")
            st.write("Includes every uploaded student row, badge counts, campaign progress, status, profile name and any verification message.")
            st.metric("Rows included", len(full_report))
            st.download_button(
                "Download full CSV report",
                report_generator.to_csv_bytes(full_report),
                "skilltrack_full_report.csv", "text/csv", type="primary", use_container_width=True,
            )
    with right:
        with st.container(border=True):
            st.markdown("### Completed students")
            st.write("Includes only students whose verified badge count meets the currently selected campaign requirement.")
            st.metric("Completed students", len(completed_report))
            st.download_button(
                "Download completed students CSV",
                report_generator.to_csv_bytes(completed_report),
                "skilltrack_completed_students.csv", "text/csv", disabled=completed_report.empty,
                use_container_width=True,
            )
    with st.expander("Preview full report", expanded=False):
        st.dataframe(full_report, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- help
def page_help():
    hero("About SkillTrack", "A coordinator workspace for checking public Google Skills profiles and monitoring campaign badge progress.", "GUIDE & METHODOLOGY")

    st.markdown("### What each section does")
    features = [
        ("Dashboard", "A quick overview of the student list, verification coverage, campaign completion and latest results."),
        ("Upload Student CSV", "Imports the coordinator's student list, detects columns, validates profile links and identifies duplicate URLs."),
        ("Verify Profiles", "Checks valid public profile URLs sequentially, applies retries and keeps partial results when paused."),
        ("Student Results", "Searches and filters student records, explains verification statuses and displays each detected badge."),
        ("Campaign Statistics", "Summarises profile verification coverage, completion rate, badge distribution and status counts."),
        ("Export Reports", "Creates a full student report or a completed-only CSV for coordinator follow-up."),
    ]
    for title, description in features:
        st.markdown(f"**{title}**  \n{description}")

    st.markdown("### Recent activity and retrying checks")
    st.markdown(
        "The dashboard keeps a short activity history for the current session. It records the student, "
        "check time and result for each newly completed profile check. Use **Retry failed profiles** "
        "to run only profiles with a previous retryable failure; profiles that have not been checked "
        "are available under **Pending profiles**."
    )

    st.markdown("### Badge counting methodology")
    st.markdown(
        "SkillTrack counts links matching the Google Skills public-profile badge URL pattern "
        "`/public_profiles/<profile-id>/badges/<badge-id>`. Only badges associated with the profile being checked are counted. "
        "Duplicate badge titles are counted once. Course links, recommendations and unrelated page content are ignored. "
        "A zero-badge result is accepted only when the returned page identity can be confirmed."
    )

    st.markdown("### Verification modes")
    st.markdown(
        "- **Any N unique badges:** a student completes the campaign after earning the configured number of unique badges.\n"
        "- **Specific required badges:** a student completes the campaign only after earning every configured title."
    )
    status_guide()

    st.markdown("### Data handling and privacy")
    st.markdown(
        "The uploaded CSV is read in memory and is not modified or written to disk by SkillTrack. "
        "The data is still processed by the machine or server hosting the app. A public Streamlit URL is not private. "
        "Use Streamlit access controls, a university-managed authenticated host or a local run before uploading real student information. "
        "Clear the current session when the work is complete."
    )

    st.markdown("### Known limitations")
    st.markdown(
        "- Only public Google Skills profiles can be verified; private profiles and sign-in redirects are marked unavailable.\n"
        "- Google may rate-limit requests. Increase the delay and retry later when this happens.\n"
        "- If Google changes its page structure, affected profiles are marked NEEDS REVIEW instead of being assigned a zero badge count.\n"
        "- JavaScript rendering is optional and requires a separate Playwright/Chromium installation."
    )


def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    sidebar()
    pages = {
        "Dashboard": page_dashboard,
        "Upload Student CSV": page_upload,
        "Verify Profiles": page_verify,
        "Student Results": page_results,
        "Campaign Statistics": page_stats,
        "Export Reports": page_export,
        "About / Help": page_help,
    }
    pages.get(st.session_state.get("page", "Dashboard"), page_dashboard)()


main()
