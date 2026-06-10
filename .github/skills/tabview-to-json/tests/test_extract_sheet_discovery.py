from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).parent.parent
EXTRACT = ROOT / "scripts" / "extract.py"


WORKBOOK_XML = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Status" sheetId="1" r:id="rId1"/>
    <sheet name="_ListVals" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>
"""


WORKBOOK_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet2.xml"/>
</Relationships>
"""


ROOT_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                Target="xl/workbook.xml"/>
</Relationships>
"""


CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""


SHEET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>ColA</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>v1</t></is></c>
    </row>
  </sheetData>
</worksheet>
"""


def _write_two_sheet_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", ROOT_RELS_XML)
        zf.writestr("xl/workbook.xml", WORKBOOK_XML)
        zf.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS_XML)
        zf.writestr("xl/worksheets/sheet1.xml", SHEET_XML)
        zf.writestr("xl/worksheets/sheet2.xml", SHEET_XML)


def _run_extract(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(EXTRACT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def test_invalid_sheet_surfaces_missing_sheet_error(tmp_path):
    xlsx_path = tmp_path / "discovery.xlsx"
    _write_two_sheet_xlsx(xlsx_path)

    result = _run_extract(str(xlsx_path), "--sheet", "Missing")

    assert result.returncode == 1
    assert "Sheet 'Missing' not found." in result.stderr
    assert "Available: Status, _ListVals" in result.stderr
    assert "Server failed to start" not in result.stderr


def test_dummy_sheet_discovery_prints_available_sheets(tmp_path):
    xlsx_path = tmp_path / "discovery.xlsx"
    _write_two_sheet_xlsx(xlsx_path)

    result = _run_extract(str(xlsx_path), "--sheet", "_dummy_")

    assert result.returncode == 0
    assert "Available sheets: Status, _ListVals" in result.stdout
    assert result.stderr == ""