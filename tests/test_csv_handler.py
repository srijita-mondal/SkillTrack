import pytest
from csv_handler import load_csv, detect_columns, build_students, summarize_issues, CSVError
from report_generator import build_report, to_csv_bytes
from progress_tracker import build_results_df

U1 = "https://www.skills.google/public_profiles/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
U2 = "https://www.skills.google/public_profiles/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
CSV = (f"Roll No,Full Name,Email Address,Google Skills Profile URL,Dept\n1,Ana,a@x.edu,{U1},CS\n"
       f"2,Bo,b@x.edu,{U2}/,IT\n,,,,\n3,Cy,,{U1},CS\n4,Di,,nonsense,EE\n")


def test_detects_common_columns():
    m = detect_columns(load_csv(CSV))
    assert m == {"url": "Google Skills Profile URL", "id": "Roll No", "name": "Full Name", "email": "Email Address"}


def test_detects_url_column_by_content():
    assert detect_columns(load_csv(f"A,B\nx,{U1}\ny,{U2}\n"))["url"] == "B"


def test_empty_and_header_only_files():
    for bad in ["", "   \n", "a,b\n", "a,b\n,\n"]:
        with pytest.raises(CSVError):
            load_csv(bad)


def test_missing_url_column_raises():
    with pytest.raises(CSVError):
        build_students(load_csv("Name\nAna\n"), {"url": None})


def test_students_validation_duplicates_empty_rows():
    df = load_csv(CSV)
    assert df.attrs["empty_rows_dropped"] == 1
    st = build_students(df, detect_columns(df))
    assert summarize_issues(st) == {"rows": 4, "valid": 3, "invalid": 1, "duplicates": 1}
    assert st["Profile URL"][1] == U2                      # trailing slash normalised
    assert "orig: Dept" in st.columns                      # original data kept


def test_no_invented_student_info():
    df = load_csv(f"URL\n{U1}\n")
    st = build_students(df, detect_columns(df))
    assert st.loc[0, "Student ID"] == "" and st.loc[0, "Student Name"] == "" and st.loc[0, "Email"] == ""


def test_semicolon_delimiter_and_bom():
    df = load_csv(("\ufeffName;Profile URL\nAna;" + U1).encode("utf-8"))
    assert detect_columns(df)["url"] == "Profile URL"


def test_report_export_excel_friendly_and_safe():
    df = load_csv(CSV.replace("Ana", "=HYPERLINK(1)"))
    st = build_students(df, detect_columns(df))
    res = build_results_df(st, {})
    data = to_csv_bytes(build_report(res))
    assert data.startswith(b"\xef\xbb\xbf") and b"'=HYPERLINK" in data
    assert "Completion Percentage" in data.decode("utf-8-sig")
    assert len(build_report(res, completed_only=True)) == 0


def test_csv_upload_limit_is_enforced(monkeypatch):
    import config

    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 12)
    with pytest.raises(CSVError, match="upload limit"):
        load_csv(b"Name,URL\n" + b"x" * 20)


def test_spreadsheet_formula_protection_handles_leading_whitespace():
    from report_generator import _safe

    assert _safe("  =HYPERLINK(1)") == "'  =HYPERLINK(1)"
    assert _safe("\t@SUM(A1:A2)") == "'\t@SUM(A1:A2)"


def test_malformed_csv_returns_actionable_error():
    with pytest.raises(CSVError, match="could not read this CSV"):
        load_csv(b'Name,Profile URL\n"unterminated value,https://example.com\n')
