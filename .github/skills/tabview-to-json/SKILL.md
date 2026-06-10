---
name: tabview-to-json
description: >
  Extracts rows from CSV, xlsx, and xlsm files into a JSON array using
  scripts/extract.py as the agent-facing CLI. Supports headless extraction,
  Python filter expressions, column selection, multi-sheet workbook
  extraction, and an optional localhost browser viewer via
  --view. Use this skill whenever a user
  wants to convert a spreadsheet or CSV to JSON, filter tabular data, extract
  specific columns or sheets from xlsx/xlsm files, render/view tabular data in a
  browser, or pipe tabular data into another tool. Trigger: /tabview-to-json
  or when user mentions CSV, xlsx, xlsm, spreadsheet, tabular data, "export to JSON",
  "render the table", "show me the data", or "open the viewer".
---

# tabview-to-json

**Bundled scripts** (always run these — do not write your own CSV/xlsx parser):
- `scripts/extract.py` — headless CLI: extracts to JSON, optional `--view` to open browser
- `scripts/csvseljson.py` — internal viewer server used by `extract.py` and optional manual viewer support

For agent workflows, always use the `extract.py` entrypoint, either as `python scripts/extract.py ...` or `python -m scripts ...` after `cd` into the skill directory. Only use `python -m scripts view ...` when the user explicitly wants a manual browser session.

**Reference files** (read when needed):
- `reference/filter-syntax.md` — `--where` expression guide
- `reference/api-contract.md` — `/data` endpoint spec
- `reference/error-playbook.md` — errors + fixes
- `agent.md` — decision tree, integration patterns

---

## Python Command

In the VS Code terminal on this machine, use `python` directly on Windows. Do not spend extra tool calls probing `py` versus `python` unless `python` actually fails. On the team Linux server the interpreter is `/bin/python3.8` (or `python3`); tabview needs no extra packages.

> **Terminal guardrail:** Never run `python` without a script argument or `-c`. In VS Code/Copilot terminal sessions it opens an interactive REPL, and later shell commands can get interpreted as Python input.

```powershell
# Windows — preferred in this workspace
python scripts\extract.py data.csv --out result.json
python -m scripts view result.json
```

```bash
# macOS/Linux
python3 scripts/extract.py data.csv --out result.json
python3 -m scripts view result.json
```

If `python` is unavailable in a different Windows environment, fall back to `py` or a full interpreter path.

---

## Script Location

The scripts live in the skill directory's `scripts/` subfolder, which is a Python package. You read this SKILL.md from disk — use that file's directory as the skill dir, then `cd` there and run as a module:

```
# All platforms — cd to the directory containing this SKILL.md, then:
python -m scripts data.csv --out result.json
python -m scripts view result.json
```

Use `python` on Windows, `python3` on macOS/Linux.

---

## Step 1 — Extract to JSON

Run the bundled script directly. Do NOT write your own csv/xlsx parsing code.

```
# cd to the directory containing this SKILL.md, then:

# CSV, all rows
python -m scripts data.csv --out result.json

# xlsx, filtered, specific columns
python -m scripts employees.xlsx \
  --sheet Staff \
  --where "int(Age or 0) > 18 and Dept == 'Sales'" \
  --cols EmpID Age Dept Office \
  --out records.json
```

Use `python` on Windows, `python3` on macOS/Linux.

> **SAS WHERE syntax** is accepted and auto-translated (e.g. `Dept = 'Sales' AND Age > '50'`). `BETWEEN x AND y` is not supported — use Python: `x <= float(COL or 0) <= y`.

`extract.py` starts the viewer server, waits for it, fetches `/data`, applies filters, kills server, and writes JSON. No browser. No extra steps.

If `extract.py` exits with `Server failed to start`, retry once with `--port 0` and inspect `extract.py` stderr. If it fails again, tell the user to check firewall or antivirus software that may be blocking loopback connections. Do not switch to a different parser or write custom CSV/xlsx code.

---

## Step 2 — Optional Browser Viewer

Keep JSON extraction headless by default. Only add `--view` when the user explicitly wants to inspect the extracted data in a browser.

```
# cd to skill dir, then:
python -m scripts data.csv --out result.json --view
python -m scripts employees.xlsx --sheet Staff --out result.json --view

# Open an already-extracted JSON file
python -m scripts view result.json
```

The viewer blocks until Ctrl+C. Tell the user: `"Table viewer running at http://127.0.0.1:<port>/ — Ctrl+C to stop."`

## Multi-Sheet Extraction

To combine all rows from multiple sheets into one JSON array, extract each sheet separately then merge:

```
# cd to skill dir, then:
python -m scripts data.xlsx --sheet Sheet1 --out sheet1.json
python -m scripts data.xlsx --sheet Sheet2 --out sheet2.json
python -c "import json; a=json.load(open('sheet1.json')); b=json.load(open('sheet2.json')); json.dump(a+b, open('combined.json','w'))"
```

Note: rows from different sheets will have different column sets (they're just merged into one flat array). If the user wants them labelled per sheet, add a `_sheet` key before merging.

---

### Chrome DevTools MCP mode (interactive filtering)

When Chrome DevTools MCP is available and the user wants to apply filters visually:

1. Start viewer in background — Windows: `Start-Job { python -m scripts view FILE --port 8765 --no-open }`
2. `navigate_page(url="http://127.0.0.1:8765")`
3. Apply filter: `fill(selector="#formula", value="Age > 50 and Dept = 'Sales'")` + `press_key("Control+Enter")`
4. Switch sheet: `evaluate_script("document.querySelectorAll('.tab')[1].click()")`
5. Fetch result: `curl -s http://127.0.0.1:8765/data` or `urllib.request.urlopen(...)`

No Chrome DevTools MCP? Start `python -m scripts view FILE --no-open` yourself and pass the printed URL to the user.

---

## Output Format

All values are strings. Missing cell = `""`.

```json
[
  {"EmpID": "001-001", "Age": "34", "Dept": "Sales", "Office": "NYC"},
  ...
]
```

Cast numeric when needed: `int(r["Age"] or 0)`.

---

## Key Flags (scripts/extract.py)

> **NEVER combine `--raw-top` and `--header-row` in one command.**
> `--raw-top` = probe pass (returns raw rows with `_col` indices). `--header-row` = extract pass. Always two separate commands.

| Flag | Description |
|---|---|
| `--sheet NAME\|INT` | xlsx sheet (name or 0-based index) |
| `--where EXPR` | Python boolean filter; column names are variables |
| `--cols COL ...` | Keep only these columns |
| `--out FILE` | Write JSON to file (default: stdout) |
| `--view` | After extraction, open localhost viewer (requires `--out`) |
| `--port INT` | Server port (0 = auto) |
| `--indent INT` | JSON indent depth (0 = compact) |
| `--raw-top PCT` | Return first PCT% of rows as raw arrays. Each row: `{"_row": N, "_col": [0,1,...], "_cells": [...]}`. Use `_col` indices with `--cols` to avoid re-typing column names. |
| `--header-row N` | Use row N (1-based) as header, bypassing auto-detection. Use after `--raw-top` probe. |

> **PowerShell 5.1 and `--where`:** If the filter contains backslash-escaped single quotes such as `row.get(\'Manager(s)\', \'\')`, `extract.py` receives an invalid Python expression and exits with a syntax error. Use a here-string instead:
>
> ```powershell
> $where = @'
> 'Jordan Lee' in str(row.get('Manager(s)', ''))
> '@
> python -m scripts file.xlsm --sheet Status --header-row 6 --where $where --cols 1 2 --out result.json
> ```

> **Non-ASCII or special-char headers:** use `_col` index from the probe in `--cols` (e.g. `--cols 0 3 7`). Avoids Unicode/encoding drift when retyping column names.
>
> **Duplicate headers:** the first occurrence keeps its original name; later duplicates are suffixed as ` [2]`, ` [3]`, and so on during extraction. Index-based `--cols` is still the safest choice when the header row repeats labels like `Project Name`.

---

## Supported Formats

| Format | Support | Notes |
|---|---|---|
| `.csv` | Full | Auto-detects delimiter |
| `.xlsx` | Full | All sheets; `--sheet` for one |
| `.xlsm` | Full | Parsed directly as zip/XML (macros ignored); no Excel required |
| `.xls` | None | Open in Excel and Save As `.xlsx` first |

> **Header auto-detection:** Headers at non-row-1 positions are detected automatically when the header row is wide enough or otherwise visually dense.
> The first sufficiently dense row of short text labels is used as the header; sparse group-label rows are skipped.
> For narrower 3-4 column tables or ambiguous preamble layouts, prefer the explicit `--raw-top` → `--header-row` workflow instead of relying on auto-detect.
> Metadata and preamble rows above it are skipped silently.
>
> For `.xlsm`/`.xlsx` files with unknown structure, use this exact workflow in this exact order: `--sheet _dummy_` → `--raw-top` → `--header-row`.
> Do not skip or reorder these steps, and do not invent substitute flags like `--probe` or `--sheet-info`.
>
> **Step 0 — Discover sheets:** For unknown-structure `.xlsm` discovery, do this even if the prompt mentions a likely sheet name such as `Status`. The point is to verify the workbook structure before trusting the name.
> Run with a nonexistent sheet name to print the available list cleanly (cd to skill dir first):
> ```
> python -m scripts file.xlsm --sheet _dummy_
> # Output: Available sheets: _Enable_Macros_, _ListVals, Status, Comments, ...
> ```
> This discovery probe is expected to print sheet names and return successfully. Pick the sheet whose name best matches what the user is looking for. Skip sheets starting with `_` (those are metadata/helper sheets). Prefer descriptive names like "Status", "Data", "Report" over generic ones.
>
> **Step 1 — Probe:** `--sheet <chosen_sheet> --raw-top 5` to see the first rows as raw arrays. The sheet name discovered in Step 0 must be included here — omitting `--sheet` probes the first sheet, which is often a cover or instructions page.
> **Step 2 — Identify:** Read the probe output (`_row` + `_cells`). Find the row where `_cells` contains short label-like strings across many columns — that's the header row. Do not guess the header row from error output or workbook noise.
> **Step 3 — Extract:** `--sheet <chosen_sheet> --header-row N` to extract using the identified header row. `N` must come from the `_row` value you just probed.
>
> **Preferred second pass when filtering Jordan Lee from the Status sheet:**
> ```
> python -m scripts file.xlsm --sheet Status --header-row 6 \
>   --where "'Jordan Lee' in str(row.get('Manager(s)', ''))" \
>   --cols 1 2 9 12 14 \
>   --out result.json
> ```
> Use `row.get(...)` for the special-character filter column and `_col` indices for `--cols` so the second pass stays one-shot and robust.
>
> If the user asks only for Record ID and Title, use `--cols 1 2`. Do not add Record Name, Project Name, or Manager columns unless the user explicitly asked for them.
>
> **Unknown-structure guardrail:** Do not invent flags like `--probe` or `--sheet-info`. They do not exist in `extract.py`. If discovery is needed, the only supported discovery path is `--sheet _dummy_` first and `--raw-top` second.

---

## Error Quick Reference

| Error | Fix |
|---|---|
| `extract.py not found` | `cd` to skill dir (directory containing this SKILL.md), then run `python -m scripts` |
| `Sheet 'X' not found` | Check the `Available:` list in stderr, or use `--sheet _dummy_` to print the sheet list directly |
| Exit code 3 | Fix `--where` expr; test it with `python -c` instead of opening an interactive REPL |
| `Server failed to start on port X` | If the failed command pinned a fixed `--port`, retry once with `--port 0`. If the command already omitted `--port` or used `--port 0`, inspect stderr and check firewall or antivirus software blocking localhost loopback. |
| `0 rows` after filter | Relax condition; cast numeric: `int(Age or 0)` |
| `.xls` rejected | Save as `.xlsx` in Excel |
| Port in use | Use `--port 0` |
| `python: command not found` (Windows) | Fall back to `py` or a full interpreter path |
| `--view` with no `--out` | Add `--out result.json` |
| extract.py timeout on `.csv` | Retry with `--port 0` and inspect stderr; do not switch tools |
| `not allowed with argument --raw-top` | Remove `--raw-top`; re-run with `--header-row N` only |

Full table → `reference/error-playbook.md`
