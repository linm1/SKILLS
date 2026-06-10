"""Tests for SAS WHERE translation and column index resolution."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from extract import _translate_sas_where, _resolve_cols, _select_cols


class TestTranslateSasWhere:
    def test_bare_equals(self):
        assert _translate_sas_where("SEX = 'F'") == "SEX == 'F'"

    def test_caret_ne(self):
        result = _translate_sas_where("ARM ^= 'Placebo'")
        assert "!=" in result

    def test_ne_keyword(self):
        result = _translate_sas_where("ARM NE 'Placebo'")
        assert "!=" in result

    def test_in_operator(self):
        assert _translate_sas_where("ARM IN ('A', 'B')") == "ARM in ('A', 'B')"

    def test_not_in_operator(self):
        assert _translate_sas_where("ARM NOT IN ('A', 'B')") == "ARM not in ('A', 'B')"

    def test_contains_operator(self):
        assert _translate_sas_where("NAME CONTAINS 'foo'") == "'foo' in NAME"

    def test_and_keyword(self):
        result = _translate_sas_where("SEX = 'F' AND AGE > '50'")
        assert " and " in result

    def test_or_keyword(self):
        result = _translate_sas_where("ARM = 'A' OR ARM = 'B'")
        assert " or " in result

    def test_where_prefix_stripped(self):
        result = _translate_sas_where("WHERE SEX = 'F'")
        assert not result.strip().lower().startswith("where")

    def test_case_insensitive_keywords(self):
        result = _translate_sas_where("sex = 'f' and age > '50'")
        assert " and " in result

    def test_string_literal_protected(self):
        result = _translate_sas_where("COUNTRY = 'US=A'")
        assert "'US=A'" in result

    def test_ge_not_mangled(self):
        result = _translate_sas_where("AGE >= 50")
        assert ">=" in result and ">>=" not in result

    def test_le_not_mangled(self):
        result = _translate_sas_where("AGE <= 50")
        assert "<=" in result

    def test_pure_python_passthrough(self):
        expr = "int(AGE or 0) > 50 and SEX == 'F'"
        result = _translate_sas_where(expr)
        # Should not crash and should still be evaluatable
        assert result is not None

    def test_not_in_not_reprocessed_by_in(self):
        # NOT IN should not become 'not in in' or similar
        result = _translate_sas_where("ARM NOT IN ('A')")
        assert result == "ARM not in ('A')"
        assert result.count("in") == 1  # exactly one 'in'


class TestResolveCols:
    def test_integer_resolves_to_col_name(self):
        keys = ["名前", "AGE", "備考"]
        assert _resolve_cols(["0"], keys) == ["名前"]
        assert _resolve_cols(["2"], keys) == ["備考"]

    def test_name_passthrough(self):
        keys = ["A", "B", "C"]
        assert _resolve_cols(["B"], keys) == ["B"]

    def test_mixed_index_and_name(self):
        keys = ["名前", "AGE", "備考"]
        assert _resolve_cols(["0", "AGE"], keys) == ["名前", "AGE"]

    def test_negative_index_treated_as_name(self):
        keys = ["A", "B", "C"]
        result = _resolve_cols(["-1"], keys)
        assert result == ["-1"]  # not resolved — treated as literal name

    def test_out_of_range_treated_as_name(self):
        keys = ["A", "B"]
        result = _resolve_cols(["99"], keys)
        assert result == ["99"]


class TestSelectCols:
    def test_empty_rows(self):
        assert _select_cols([], ["0"]) == []

    def test_unknown_col_warning(self, capsys):
        rows = [{"A": "1", "B": "2"}]
        _select_cols(rows, ["TYPO"])
        captured = capsys.readouterr()
        assert "unknown" in captured.err.lower()
