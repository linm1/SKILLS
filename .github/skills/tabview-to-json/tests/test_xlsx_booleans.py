import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from csvseljson import parse_xlsx


WORKBOOK_XML = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Flags" sheetId="1" r:id="rId1"/>
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
      <c r="A1" t="inlineStr"><is><t>FLAG</t></is></c>
      <c r="B1" t="inlineStr"><is><t>NAME</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="b"><v>1</v></c>
      <c r="B2" t="inlineStr"><is><t>Row 1</t></is></c>
    </row>
  </sheetData>
</worksheet>
"""


def _write_boolean_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", ROOT_RELS_XML)
        zf.writestr("xl/workbook.xml", WORKBOOK_XML)
        zf.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS_XML)
        zf.writestr("xl/worksheets/sheet1.xml", SHEET_XML)


def test_parse_xlsx_boolean_cells_are_returned_as_strings(tmp_path):
    xlsx_path = tmp_path / "boolean-cells.xlsx"
    _write_boolean_xlsx(xlsx_path)

    rows = parse_xlsx(str(xlsx_path), sheet="Flags", header_row=1)["Flags"]

    assert rows == [{"FLAG": "1", "NAME": "Row 1"}]