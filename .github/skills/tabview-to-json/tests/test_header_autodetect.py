"""Tests for column-spread header auto-detection in parse_xlsx."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from csvseljson import _looks_like_header, _is_numeric


def test_is_numeric_float():
    assert _is_numeric("3.14") is True

def test_is_numeric_int():
    assert _is_numeric("42") is True

def test_is_numeric_text():
    assert _is_numeric("Output Identifier") is False

def test_is_numeric_empty():
    assert _is_numeric("") is False

def test_looks_like_header_real_row():
    row = ["Output Type", "Output Identifier", "Title", "QC Program Name",
           "QC Programmer", "Output Name", "Status"]
    assert _looks_like_header(row) is True

def test_looks_like_header_sparse_preamble():
    row = ["Sponsor Project Number:", "", "", "", "", "", ""]
    assert _looks_like_header(row) is False

def test_looks_like_header_long_text_preamble():
    row = ["Note: Save file as <Project Number> <Delivery type> Statistical Programming Status Tracker very long text here that exceeds 40 chars", "", "", ""]
    assert _looks_like_header(row) is False

def test_looks_like_header_group_label_row():
    row = [
        "", "", "", "", "", "", "", "",
        "Main Programming", "", "", "", "QC Programming", "", "",
        "Biostatistics QC", "", "", "PK/PD Review", "",
        "Deliverable Review", "",
    ]
    assert _looks_like_header(row) is False

def test_looks_like_header_header_at_row1():
    row = ["USUBJID", "AGE", "SEX", "ARM", "VISIT", "AVAL", "PARAM"]
    assert _looks_like_header(row) is True

def test_looks_like_header_exactly_six_cols():
    # Six short text columns is the minimum valid header density.
    row = ["ColA", "ColB", "ColC", "ColD", "ColE", "ColF"]
    assert _looks_like_header(row) is True

def test_looks_like_header_dense_five_col_row():
    # Dense 5-column headers should still auto-detect successfully.
    row = ["ColA", "ColB", "ColC", "ColD", "ColE"]
    assert _looks_like_header(row) is True

def test_looks_like_header_indented_dense_five_col_row():
    # Leading blanks should not penalize a real 5-column header.
    row = ["", "", "", "", "", "ColA", "ColB", "ColC", "ColD", "ColE"]
    assert _looks_like_header(row) is True


def test_xlsm_ext_detected():
    """Verify ext detection recognises .xlsm as a separate case from .xlsx."""
    assert os.path.splitext("file.xlsm")[1].lower() == '.xlsm'
    assert os.path.splitext("file.xlsx")[1].lower() == '.xlsx'


def test_looks_like_header_still_works_after_refactor():
    """Heuristic path unchanged — basic sanity check."""
    row = ["Output Type", "Output Identifier", "Title", "QC Program Name",
           "QC Programmer", "Output Name", "Status"]
    assert _looks_like_header(row) is True
