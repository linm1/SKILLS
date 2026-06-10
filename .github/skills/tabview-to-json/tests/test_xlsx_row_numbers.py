import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from csvseljson import parse_xlsx


WORKBOOK_XML = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Status" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""


WORKBOOK_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
                Target="worksheets/sheet1.xml"/>
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
</Types>
"""


SHEET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>Metadata</t></is></c>
    </row>
    <row r="3">
      <c r="A3" t="inlineStr"><is><t>ColA</t></is></c>
      <c r="B3" t="inlineStr"><is><t>ColB</t></is></c>
      <c r="C3" t="inlineStr"><is><t>ColC</t></is></c>
      <c r="D3" t="inlineStr"><is><t>ColD</t></is></c>
      <c r="E3" t="inlineStr"><is><t>ColE</t></is></c>
    </row>
    <row r="4">
      <c r="A4" t="inlineStr"><is><t>v1</t></is></c>
      <c r="B4" t="inlineStr"><is><t>v2</t></is></c>
      <c r="C4" t="inlineStr"><is><t>v3</t></is></c>
      <c r="D4" t="inlineStr"><is><t>v4</t></is></c>
      <c r="E4" t="inlineStr"><is><t>v5</t></is></c>
    </row>
  </sheetData>
</worksheet>
"""


def _write_sparse_row_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", ROOT_RELS_XML)
        zf.writestr("xl/workbook.xml", WORKBOOK_XML)
        zf.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS_XML)
        zf.writestr("xl/worksheets/sheet1.xml", SHEET_XML)


def test_raw_probe_preserves_actual_sheet_row_numbers(tmp_path):
    xlsx_path = tmp_path / "sparse-rows.xlsx"
    _write_sparse_row_xlsx(xlsx_path)

    rows = parse_xlsx(str(xlsx_path), sheet="Status", raw_top=100)["Status"]

    assert rows[1]["_row"] == 3
    assert rows[2]["_row"] == 4


def test_header_row_uses_actual_sheet_row_number(tmp_path):
    xlsx_path = tmp_path / "sparse-rows.xlsx"
    _write_sparse_row_xlsx(xlsx_path)

    rows = parse_xlsx(str(xlsx_path), sheet="Status", header_row=3)["Status"]

    assert rows == [{"ColA": "v1", "ColB": "v2", "ColC": "v3", "ColD": "v4", "ColE": "v5"}]