"""Load coordinator CSVs, detect/map columns, validate URLs and normalise student records.
The uploaded data is never modified or written to disk."""
import csv
import io
import re

import pandas as pd

import config
from scraper import validate_profile_url

ALIASES = {
    "url": ["googleskillsprofileurl", "googleskillsprofile", "skillsprofileurl", "publicprofileurl",
            "publicprofile", "profileurl", "profilelink", "googlecloudskillsboostprofile",
            "skillsboostprofile", "skillsboostprofileurl", "url", "link", "profile"],
    "id": ["studentid", "id", "rollno", "rollnumber", "enrollmentno", "enrollmentnumber",
           "enrollment", "regno", "registrationnumber", "universityid", "sid"],
    "name": ["studentname", "name", "fullname", "candidatename", "participantname"],
    "email": ["email", "emailaddress", "emailid", "mail", "studentemail"],
}


class CSVError(ValueError):
    """Raised for problems the coordinator can fix (empty file, missing column, bad encoding...)."""


def _norm(header):
    return re.sub(r"[^a-z0-9]", "", str(header).lower())


def load_csv(source):
    """Read CSV bytes / file-like object into a DataFrame of strings. Empty rows are dropped
    (count stored in df.attrs['empty_rows_dropped'])."""
    raw = source.read() if hasattr(source, "read") else source
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    elif isinstance(raw, (bytearray, memoryview)):
        raw = bytes(raw)
    if not isinstance(raw, bytes):
        raise CSVError("The uploaded file could not be read. Please choose a CSV file and try again.")
    if len(raw) > config.MAX_UPLOAD_BYTES:
        limit_mb = config.MAX_UPLOAD_BYTES / (1024 * 1024)
        raise CSVError(f"The CSV is larger than the {limit_mb:g} MB upload limit. Split the file and try again.")
    if not raw or not raw.strip():
        raise CSVError("The file is empty.")
    text = None
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeError:
            continue
    if text is None:
        raise CSVError("Could not decode the file. Save it as CSV UTF-8 and try again.")
    try:
        df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, sep=None, engine="python")
    except pd.errors.EmptyDataError:
        raise CSVError("The file contains no data.")
    except (pd.errors.ParserError, csv.Error, UnicodeError, ValueError, TypeError) as exc:
        raise CSVError(
            "SkillTrack could not read this CSV. Check that the file has a header row, "
            "consistent columns and valid quoting, then save it as CSV UTF-8 and try again."
        ) from exc
    except Exception as exc:
        # Keep parser/library details out of the normal coordinator-facing message.
        raise CSVError("An unexpected problem occurred while reading this CSV. Please check the file and try again.") from exc
    df.columns = [str(c).strip() for c in df.columns]
    df = df.apply(lambda col: col.str.strip())
    blank = (df == "").all(axis=1)
    dropped = int(blank.sum())
    df = df[~blank].reset_index(drop=True)
    if df.empty:
        raise CSVError("The file has a header but no student rows.")
    df.attrs["empty_rows_dropped"] = dropped
    return df


def detect_columns(df):
    """Best-effort mapping {'url','id','name','email'} -> column name or None."""
    headers = {c: _norm(c) for c in df.columns}
    mapping, used = {}, set()

    def pick(kind):
        for alias in ALIASES[kind]:                       # exact alias match, in priority order
            for col, h in headers.items():
                if h == alias and col not in used:
                    return col
        if kind == "url":                                  # looser header match
            for col, h in headers.items():
                if col not in used and any(k in h for k in ("profile", "url", "link")):
                    return col
            for col in df.columns:                         # content-based: cells look like profile links
                if col not in used and df[col].astype(str).str.contains("public_profiles", case=False).mean() > 0.5:
                    return col
        if kind == "name":
            for col, h in headers.items():
                if col not in used and "name" in h:
                    return col
        return None

    for kind in ("url", "id", "name", "email"):
        col = pick(kind)
        mapping[kind] = col
        if col:
            used.add(col)
    return mapping


def build_students(df, mapping):
    """Return a normalised student table. Original columns not used for mapping are kept as
    'orig: <column>' so they can be exported. Raises CSVError if the URL column is missing."""
    url_col = mapping.get("url")
    if not url_col or url_col not in df.columns:
        raise CSVError("Select the column that contains the Google Skills profile URL.")

    def col(kind):
        c = mapping.get(kind)
        return df[c] if c and c in df.columns else pd.Series([""] * len(df), index=df.index)

    out = pd.DataFrame({
        "Row": range(2, len(df) + 2),                      # spreadsheet row number (header = row 1)
        "Student ID": col("id").astype(str),
        "Student Name": col("name").astype(str),
        "Email": col("email").astype(str),
    }, index=df.index)

    checks = [validate_profile_url(u) for u in df[url_col].astype(str)]
    out["Original URL"] = df[url_col].astype(str)
    out["Profile URL"] = [norm if ok else raw for (ok, norm, _), raw in zip(checks, out["Original URL"])]
    out["URL Valid"] = [ok for ok, _, _ in checks]
    out["URL Error"] = [err or "" for _, _, err in checks]
    out["Duplicate Profile"] = out["URL Valid"] & out.duplicated(subset="Profile URL", keep="first")

    mapped = {c for c in mapping.values() if c}
    for c in df.columns:
        if c not in mapped:
            out[f"orig: {c}"] = df[c]
    return out.reset_index(drop=True)


def summarize_issues(students):
    """Counts shown to the coordinator after upload."""
    return {
        "rows": len(students),
        "valid": int(students["URL Valid"].sum()),
        "invalid": int((~students["URL Valid"]).sum()),
        "duplicates": int(students["Duplicate Profile"].sum()),
    }
