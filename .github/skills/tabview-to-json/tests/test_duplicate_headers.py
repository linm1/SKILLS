import json
import sys
from pathlib import Path
import subprocess

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from csvseljson import _dedupe_headers


ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "scripts" / "extract.py"
FILE_XLSM = ROOT / "evals" / "files" / "file.xlsm"


def test_dedupe_headers_preserves_first_occurrence_name():
    headers = [
        "Output Identifier",
        "QC Program Name\n(.r / .sas)",
        "QC Programmer(s)",
        "QC Program Name\n(.r / .sas)",
    ]

    assert _dedupe_headers(headers) == [
        "Output Identifier",
        "QC Program Name\n(.r / .sas)",
        "QC Programmer(s)",
        "QC Program Name\n(.r / .sas) [2]",
    ]


def test_extract_xlsm_known_header_keeps_first_duplicate_column(tmp_path):
    if not FILE_XLSM.exists():
        pytest.skip("xlsm fixture missing")

    out_path = tmp_path / "result.json"
    cmd = [
        sys.executable,
        str(EXTRACT),
        str(FILE_XLSM),
        "--sheet",
        "Status",
        "--header-row",
        "6",
        "--where",
        "'Mark Lin' in str(row.get('QC Programmer(s)', ''))",
        "--cols",
        "1",
        "2",
        "9",
        "12",
        "14",
        "--out",
        str(out_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr

    rows = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(rows) == 17
    assert list(rows[0].keys()) == [
        "Output Identifier",
        "Title",
        "Output Name",
        "QC Program Name\n(.r / .sas)",
        "QC Programmer(s)",
    ]
    assert rows[0]["QC Program Name\n(.r / .sas)"] == "qc_t_lab_sum"
    assert rows[0]["QC Programmer(s)"] == "Mark Lin"