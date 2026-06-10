# tabview-to-json — Universal Agent Instructions

> Compatible with: Claude Code, GitHub Copilot Chat, Codex CLI, Antigravity, Cursor, any LLM agent with shell tool access.

## What This Package Does

Reads any `.csv`, `.xlsx`, or `.xlsm` file, optionally filters rows, and outputs a JSON array.
Primary flow:
1. **Headless** (default) — `extract.py` handles the full discover -> extract -> filter -> output workflow. No browser needed.
2. **Browser** (optional) — use `extract.py --view` or `python -m scripts view ...` for manual inspection only.

Both modes require only Python 3.8+. Zero pip installs. No Excel required — `.xlsm` is parsed directly as zip/XML (macros are ignored).
Header auto-detection works best on wider or visually dense header rows. For narrower 3-4 column tables with preamble rows, use the explicit `--raw-top` → `--header-row` workflow below.

> **Terminal guardrail:** Never run `python` without a script argument or `-c`. In VS Code/Copilot terminal sessions it opens an interactive REPL, and later shell commands can get interpreted as Python input.

---

## Files in This Package

| File | Purpose |
|---|---|
| `scripts/csvseljson.py` | Internal infrastructure — serves the local viewer and `/data` endpoint for `extract.py` |
| `scripts/extract.py` | Headless CLI — start server, fetch data, filter, write JSON |
| `agent.md` | This file — agent instructions |
| `SKILL.md` | Claude Code skill descriptor |
| `reference/filter-syntax.md` | WHERE / Python filter expression reference |
| `reference/api-contract.md` | `/data` HTTP endpoint spec |
| `reference/error-playbook.md` | Error → fix lookup table |

---

## Quickstart (Any Agent)

### Headless extraction (no browser)

Always use `extract.py` for agent workflows. Only open the browser viewer when the user explicitly asks to inspect the table visually.
On Windows in this workspace, substitute `python` for `python3` in the shell examples below.

```bash
# CSV — all rows
python scripts/extract.py data.csv --out records.json

# xlsx — first sheet, all rows
python scripts/extract.py data.xlsx --out records.json

# xlsx/xlsm — named sheet, filter, select columns
python scripts/extract.py study.xlsx \
  --sheet ADSL \
  --where "int(AGE or 0) > 50 and SEX == 'F'" \
  --cols USUBJID AGE SEX ARM \
  --out adsl_filtered.json
```

### Open viewer after extraction

```bash
# Extract + open viewer (blocks until Ctrl+C)
python scripts/extract.py data.xlsx --out result.json --view

# Open an already-extracted JSON file manually
python -m scripts view result.json
```

### Browser-based (with Chrome DevTools MCP)

```bash
# 1. Start server (background)
python -m scripts view data.xlsx --port 8765 --no-open &

# 2. Interact via DevTools or browser, then fetch result
curl -s http://127.0.0.1:8765/data | python -c "
import json,sys; d=json.load(sys.stdin)
sheet=list(d['data'].keys())[0]
print(json.dumps(d['data'][sheet], indent=2))
" > records.json

# 3. Stop server
kill %1
```

---

## Agent Decision Tree

```
User wants tabular data as JSON
│
├─ Has filter condition?
│   ├─ Simple or SAS-like: use extract.py --where
│   └─ Visual/manual filtering requested: use extract.py --view or start the browser viewer,
│      fill filter input, then fetch /data
│
├─ File type?
│   ├─ .csv  → extract.py directly
│   ├─ .xlsx → extract.py (headless) or viewer (visual)
│   ├─ .xlsm → extract.py (parsed directly; no Excel needed)
│   └─ .xls  → STOP: not supported. Ask user to save as .xlsx
│
└─ Output needed?
    ├─ File: --out path.json
    └─ Pipe to next step: stdout (omit --out)

For automated agent workflows, stop at `extract.py`. Treat `csvseljson.py` as infrastructure, not the primary entrypoint.
```

---

## Integration Patterns

### Pattern 1: Extract then process (agent pipeline)

```python
import subprocess, json

result = subprocess.run(
    ["python", "scripts/extract.py", "data.xlsx",
     "--sheet", "ADSL",
     "--where", "int(AGE or 0) > 18",
     "--indent", "0"],
    capture_output=True, text=True, check=True
)
records = json.loads(result.stdout)
# pass records to next agent task
```

### Pattern 2: Multi-sheet extraction

```python
import subprocess, json

# Get all sheets
result = subprocess.run(
    ["python", "scripts/extract.py", "study.xlsx", "--indent", "0"],
    capture_output=True, text=True
)
records = json.loads(result.stdout)

# Or fetch raw /data for all sheets at once
import urllib.request, threading, time
# Start csvseljson.py view, poll /data, split by sheet key, write per-sheet JSON
```

### Pattern 3: Pipe into another tool

```bash
python scripts/extract.py data.xlsx --sheet ADSL --indent 0 | jq '.[] | select(.ARM == "Placebo")'
python scripts/extract.py data.csv | python next_analysis.py
python scripts/extract.py data.xlsx --out - | gzip > records.json.gz
```

---

## Environment Notes

| Platform | Python command | Notes |
|---|---|---|
| Windows | `python` | In this VS Code workspace, use `python` directly. If it is unavailable in another Windows environment, fall back to `py`. |
| macOS/Linux | `python3` | `python` may be Python 2 on older systems |
| GitHub Codespaces | `python3` | Pre-installed |
| Any | `python --version` or `python3 --version` | Must be 3.8+ |

No virtual environment needed. No requirements.txt. The scripts live in `scripts/` inside the skill directory.

---

## Output Contract

```json
[
  {"USUBJID": "001-001", "AGE": "34", "SEX": "F", "ARM": "Placebo"},
  {"USUBJID": "001-002", "AGE": "51", "SEX": "M", "ARM": "Treatment A"}
]
```

- JSON array of objects, one object per row
- All values are strings (CSV/xlsx preserves original string representation)
- Missing cells → `""` (empty string)
- Column order = original file order (or `--cols` order if specified)
- Encoding: UTF-8

To convert numeric strings after extraction:
```python
records = [{**r, "AGE": int(r["AGE"] or 0)} for r in records]
```

---

## Common Agent Mistakes to Avoid

| Mistake | Correct approach |
|---|---|
| Writing your own csv/xlsx parser | Run `scripts/extract.py` — that IS the parser |
| Trying to parse xlsx with pandas | Use `scripts/extract.py` — zero deps |
| Scraping table HTML from browser | Fetch `/data` endpoint — structured JSON |
| Assuming numeric types in output | All values are strings; cast explicitly |
| Using `--sheet` with CSV input | `--sheet` only applies to xlsx |
| Keeping server running after done | Always kill with `proc.terminate()` or `kill %1` |
| Opening browser before server ready | Wait for `/data` to respond (extract.py handles this) |
| Using `--view` without `--out` | Add `--out result.json` first |
| Running bare `python` for quick inspection | Use `python -c "..."` or a script path instead. Never open an interactive REPL in automation. |
| Stopping after `Server failed to start` | If the failed command pinned a fixed `--port`, retry once with `--port 0`. Otherwise record the real failure and note possible firewall or antivirus loopback blocking. |
| **Column names with special characters or Unicode:** After `--raw-top` probe, do NOT re-type column names | Use the `_col` index from the probe output instead. Each raw row includes `_col: [0, 1, 2, ...]` parallel to `_cells`. Pass those integers directly to `--cols` (e.g. `--cols 0 3 7`). This avoids Unicode normalization drift, full/half-width confusion, and punctuation encoding errors. |

---

## Three-Step Extraction for Unknown Files

Use this workflow for `.xlsm` or `.xlsx` files with unknown structure, or when the user describes columns in natural language (e.g., "qc programmer", "output id").

For unknown-structure work, the sequence is fixed: `--sheet _dummy_` first, then `--raw-top`, then `--header-row`.
Do not skip or reorder these steps, and Do not invent flags like `--probe` or `--sheet-info`.

### When to skip this workflow

| Situation | Action |
|---|---|
| File is CSV | Go direct — `python scripts/extract.py file.csv --out result.json` |
| xlsx, user named the sheet and exact column headers | Go direct with `--sheet` and `--cols` — no probe needed |
| xlsx/xlsm with unknown structure, OR columns described in natural language | Use the 3-step workflow below |

---

### Worked Example A — xlsm with preamble rows

**Scenario:** User has `file.xlsm`, doesn't know the sheet name, wants rows for QC Programmer "Mark Lin" with columns Output Identifier, Title, Output Name, QC Program Name, QC Programmer.

Only the final `--out` file goes where the user asks. The probe writes to **stdout** — no temp file, no cleanup needed. Capture it in memory.

#### Step 0 — Discover sheets

Do this even if the prompt mentions a likely sheet name such as `Status`. In unknown-structure `.xlsm` tasks, the sheet name is still unverified until you print the available-sheet list and confirm it.

```
python scripts/extract.py file.xlsm --sheet _dummy_
```

Output:
```
Available sheets: _Enable_Macros_, _ListVals, _SharePoint, Status, Comments, Signature Page, _WorkDone, _hid
```

**Read:** This command is expected to succeed and print the sheet list. Skip sheets starting with `_` (internal tabs). `Status` matches "deliverable tracking" — pick it.

#### Step 1 — Raw probe (stdout — no temp file)

Omit `--out` so probe output goes to stdout. Capture it directly:

```python
import subprocess, json

probe = subprocess.run(
    ["python", "scripts/extract.py", "file.xlsm",
     "--sheet", "Status", "--raw-top", "5"],
    capture_output=True, text=True
)
rows = json.loads(probe.stdout)
```

```bash
# Shell: capture to variable, no file written
PROBE=$(python scripts/extract.py file.xlsm --sheet Status --raw-top 5)
# then parse $PROBE with python -c or jq
```

Probe output (condensed — only non-empty cells, first 16 columns):

```
_row=1  col0:"Sponsor Project Number:"   col3:"Parexel Project Number:"
_row=2  col0:"Sponsor Name:"             col3:"Deliverable Type:"
_row=3  col0:"Deliverable Version:"      col1:"1"   col3:"Deliverable Date:"
_row=4  (empty)
_row=5  col8:"Main Programming"          col12:"QC Programming"   col15:"Biostatistics QC"
_row=6  col0:"Output Type"              col1:"Output Identifier"   col2:"Title"
        col3:"Programming QC Method"     col8:"Main Program Name\n(.r / .sas)"
        col9:"Output Name"              col11:"Main Programmer(s)"
        col12:"QC Program Name\n(.r / .sas)"   col14:"QC Programmer(s)"
```

#### Step 2 — Identify header row and column indices

**Read:** Row 6 has dense short label strings across many columns — that's the header. Rows 1–3 are metadata (key–value pairs). Row 5 is a group label row (sparse). `header_row = 6`.
The header row value must come from the probe output's `_row` field. Do not guess it from workbook noise or unrelated error output.

Map user's requested columns to `_col` indices from row 6:
- "Output Identifier" → col **1**
- "Title" → col **2**
- "Output Name" → col **9**
- "QC Program Name" → col **12**
- "QC Programmer" → col **14**

Use indices (not re-typed names) — column 12 header contains `\n` which causes encoding drift.

#### Step 3 — Extract

No cleanup needed — probe left no files on disk.

```python
import subprocess, json

result = subprocess.run(
    ["python", "scripts/extract.py", "file.xlsm",
     "--sheet", "Status",
     "--header-row", "6",
     "--where", "'Mark Lin' in str(row.get('QC Programmer(s)', ''))",
     "--cols", "1", "2", "9", "12", "14",
     "--out", "result.json"],
    capture_output=True, text=True
)
print(result.stderr)  # e.g. "[extract] Filter: 24 → 17 rows"
```

```bash
# Shell
python scripts/extract.py file.xlsm \
  --sheet Status --header-row 6 \
  --where "'Mark Lin' in str(row.get('QC Programmer(s)', ''))" \
  --cols 1 2 9 12 14 \
  --out result.json
# stderr: [extract] Filter: 24 → 17 rows
```

**PowerShell 5.1 note:** If the model has already produced a `--where` string with backslash-escaped single quotes such as `row.get(\'QC Programmer(s)\', \'\')`, do not run it directly. Put the filter into a here-string first:

```powershell
$where = @'
'Mark Lin' in str(row.get('QC Programmer(s)', ''))
'@
python -m scripts file.xlsm --sheet Status --header-row 6 --where $where --cols 1 2 9 12 14 --out result.json
```

If the user asks only for Output Identifier and Title, use `--cols 1 2`. Do not add Output Name, QC Program Name, or QC Programmer columns unless the user explicitly asked for them.

Expected output shape (17 rows):
```json
[
  {
    "Output Identifier": "Table 14.2.3.5.1a",
    "Title": "Summary of Serum Hepcidin Over Time Full Analysis Set",
    "Output Name": "t_hepc_sum.rtf",
    "QC Program Name\n(.r / .sas)": "qc_t_lab_sum",
    "QC Programmer(s)": "Mark Lin"
  },
  ...
]
```

---

### Worked Example B — xlsx with standard header (go direct)

**Scenario:** User has `study.xlsx`, wants female subjects older than 50 from the ADSL sheet.
Sheet name and columns are known → **skip the 3-step, go direct.**

```bash
python scripts/extract.py study.xlsx \
  --sheet ADSL \
  --where "int(AGE or 0) > 50 and SEX == 'F'" \
  --cols USUBJID AGE SEX ARM \
  --out result.json
# stderr: [extract] Filter: 8 → 3 rows
```

No probe needed. Auto-detect handles standard row-1 headers. Use `int(AGE or 0)` because all values are strings — the `or 0` guards empty cells.

---

### Rules for the probe workflow

- **Use the exact discovery chain:** `--sheet _dummy_` → `--raw-top` → `--header-row`. No substitutes.
- **Do not invent flags like `--probe` or `--sheet-info`.** They are not supported by `extract.py`.
- **`_row`** is the 1-based sheet row number — pass it directly to `--header-row`. Do not count array positions.
- **`_col`** gives 0-based column indices parallel to `_cells` — pass them to `--cols`. Never re-type column names with special characters or newlines.
- **Never combine `--raw-top` and `--header-row`** in one command. Probe pass first, extract pass second.
- **Probe to stdout, not a file.** Omit `--out` on the `--raw-top` pass — capture stdout in memory. This avoids Windows temp-directory permission issues and leaves no cleanup. Only the final extraction uses `--out`.
- If the header row repeats a label, first occurrence keeps its name; later duplicates become ` [2]`, ` [3]`, etc. Index-based `--cols` sidesteps this entirely.
