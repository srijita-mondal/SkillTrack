"""Build Excel-friendly CSV reports from the results table."""
import pandas as pd

REPORT_COLUMNS = {
    "Student ID": "Student ID", "Student Name": "Student Name", "Profile URL": "Profile URL",
    "Earned Badges": "Earned Badge Count", "Required": "Required Badge Count",
    "Progress": "Completion Percentage", "Status": "Status", "Badge Titles": "Badge Titles",
    "Google Skills Name": "Google Skills Profile Name",
    "Last Checked": "Last Checked", "Error Message": "Error Message",
}


def build_report(results, completed_only=False):
    df = results[results["Status"] == "COMPLETED"] if completed_only else results
    extras = [c for c in df.columns if c.startswith("orig: ")]
    out = df[list(REPORT_COLUMNS) + extras].rename(columns=REPORT_COLUMNS).copy()
    # Unverifiable profiles keep an empty count (not 0) so they are never read as "zero badges".
    return out.reset_index(drop=True)


def _safe(value):
    """Neutralise spreadsheet formula injection (cells starting with = + - @)."""
    if isinstance(value, str) and value.lstrip(" \t\r\n")[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def to_csv_bytes(df):
    """UTF-8 with BOM so Excel opens accents correctly."""
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object or pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].map(_safe)
    return df.to_csv(index=False).encode("utf-8-sig")
