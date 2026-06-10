# Filter Syntax Reference

Two filter modes exist depending on context.

---

## Mode A: SAS-style WHERE (browser viewer)

Entered in the browser filter input. Parsed entirely in JavaScript.

### Operators

| Syntax | Meaning | Example |
|---|---|---|
| `COL = value` | Equal | `SEX = "F"` |
| `COL ^= value` | Not equal | `ARM ^= "Placebo"` |
| `COL < value` | Less than | `AGE < 65` |
| `COL > value` | Greater than | `AGE > 18` |
| `COL <= value` | Less or equal | `AVAL <= 100` |
| `COL >= value` | Greater or equal | `AGE >= 18` |
| `COL BETWEEN x AND y` | Inclusive range | `AGE BETWEEN 18 AND 65` |
| `COL IN (a, b, c)` | Set membership | `RACE IN ("WHITE", "ASIAN")` |
| `COL CONTAINS "text"` | Substring (case-insensitive) | `PARAM CONTAINS "WEIGHT"` |
| `COL = .` | Numeric missing | `AVAL = .` |
| `COL = ""` | String missing/blank | `PARAM = ""` |
| `AND` | Logical and | `AGE > 18 AND SEX = "F"` |
| `OR` | Logical or | `ARM = "A" OR ARM = "B"` |
| `NOT` | Logical not | `NOT ARM = "Placebo"` |

### Rules

- String values in `"double quotes"` or `'single quotes'`
- Column names case-insensitive (`age`, `AGE`, `Age` all match)
- Numeric comparisons: strip commas, parse as float
- Missing numeric (`.`): compare against empty string or literal `.`
- Parentheses group expressions: `(AGE > 50 OR AVAL > 100) AND SEX = "F"`

### Examples

```
AGE > 18
SEX = "F" AND ARM ^= "Placebo"
AGE BETWEEN 18 AND 65
RACE IN ("WHITE", "BLACK OR AFRICAN AMERICAN", "ASIAN")
PARAM CONTAINS "WEIGHT" AND AVAL > 0
USUBJID CONTAINS "001"
AVAL = .
NOT SEX = "M"
(ARM = "A" OR ARM = "B") AND AGE >= 18
```

---

## SAS WHERE (auto-translated by `--where`)

`extract.py --where` accepts SAS WHERE syntax and translates it to Python automatically before evaluation. SAS programmers can write natural WHERE expressions.

### Supported operators (all case-insensitive)

| SAS | Python equivalent | Example |
|-----|-------------------|---------|
| `COL = 'x'` | `COL == 'x'` | `SEX = 'F'` |
| `COL ^= 'x'` | `COL != 'x'` | `ARM ^= 'Placebo'` |
| `COL NE 'x'` | `COL != 'x'` | `ARM NE 'Placebo'` |
| `COL IN ('a','b')` | `COL in ('a','b')` | `ARM IN ('A', 'B')` |
| `COL NOT IN ('a','b')` | `COL not in ('a','b')` | `ARM NOT IN ('Placebo')` |
| `COL CONTAINS 'x'` | `'x' in COL` | `NAME CONTAINS 'Smith'` |
| `AND` | `and` | `SEX = 'F' AND AGE > '50'` |
| `OR` | `or` | `ARM = 'A' OR ARM = 'B'` |
| `NOT` (standalone) | `not` | `NOT SEX = 'F'` |
| Leading `WHERE` | stripped | `WHERE SEX = 'F'` |

### Not supported

| SAS construct | Use instead |
|---|---|
| `BETWEEN x AND y` | `x <= float(COL or 0) <= y` |

### Notes

- All values are strings — numeric comparisons require casting: `int(AGE or 0) > 50`
- Translation is logged to stderr: `[extract] SAS→Python: <translated>`
- Pure Python expressions (e.g. `int(AGE or 0) > 50 and SEX == 'F'`) pass through unchanged

---

## Mode B: Python expression (extract.py --where)

Passed to `extract.py --where "EXPR"`. Evaluated with `eval()` in a restricted namespace where each column name is a variable holding the cell's string value.

### Rules

- All column values are **strings** — cast for numeric comparison
- Missing cell = `""` (empty string)
- Standard Python operators: `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `not in`
- String methods available: `.startswith()`, `.endswith()`, `.strip()`, `.upper()`, etc.
- No imports available inside expression (builtins restricted)

### Safe numeric cast pattern

```python
int(AGE or 0) > 18          # "" → 0, avoids ValueError
float(AVAL or 0) > 100.0
int(AGE or 0) if AGE else None
```

### Examples

```python
# Numeric comparison
"int(AGE or 0) > 18"
"float(AVAL or 0) >= 100.0"
"18 <= int(AGE or 0) <= 65"

# String comparison
"SEX == 'F'"
"ARM != 'Placebo'"
"ARM in ('Treatment A', 'Treatment B')"

# String methods
"USUBJID.startswith('001')"
"PARAM.upper().find('WEIGHT') >= 0"

# Missing values
"AVAL == ''"                 # blank cell
"SEX != ''"                  # non-missing sex

# Combined
"int(AGE or 0) > 50 and SEX == 'F'"
"ARM in ('A', 'B') and float(AVAL or 0) > 0"
"(ARM == 'A' or ARM == 'B') and int(AGE or 0) >= 18"
```

### Column names with spaces or special chars

If column name contains spaces (e.g., `"Subject ID"`), it cannot be used directly as a Python identifier. Access it via the row dict instead, for example `row.get('Subject ID', '')`. When selecting columns from probed xlsx/xlsm files, prefer `_col` indices from the `--raw-top` output rather than retyping problematic header names.

---

## Comparison: SAS WHERE vs Python --where

| Feature | SAS WHERE (browser) | Python --where (extract.py) |
|---|---|---|
| Syntax | SAS-style | Python |
| String quotes | `"..."` or `'...'` | `'...'` (shell) |
| Numeric cast | Automatic | Manual: `int(X or 0)` |
| Missing | `= .` or `= ""` | `== ""` |
| Substring | `CONTAINS "text"` | `'text' in COL` |
| Range | `BETWEEN x AND y` | `x <= int(COL or 0) <= y` |
| Set | `IN (a, b)` | `COL in ('a', 'b')` |
| Regex | Not supported | Not supported |
