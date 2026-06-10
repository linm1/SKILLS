# Error Playbook

Symptom → cause → fix. One lookup table for every known failure.

Fallback rule: if `extract.py` fails, adjust the extractor inputs or the local server settings. Do not switch to custom parsing code.

---

## extract.py Errors

| Symptom | Cause | Fix |
|---|---|---|
| `File not found: data.xlsx` | Wrong path | Verify path exists: `ls data.xlsx` or `dir data.xlsx` |
| `csvseljson.py not found at ...` | extract.py can't find core script | Place `csvseljson.py` next to `extract.py` in same directory |
| `Server failed to start on port 8765` | Port already in use or script crash | Use `--port 0` (auto-pick free port); check stderr for Python traceback |
| `Sheet '99' not found.` | Index out of range | See "Available:" list in error; use correct 0-based index |
| `Sheet 'ADSL' not found.` | Name mismatch | Check exact name (case-sensitive): see "Available:" list |
| Filter `eval()` raises `NameError: name 'AGE' is not defined` | Column name not in this row/sheet | Check column name spelling matches file header exactly |
| Filter exits with code 3 | `--where` expression syntax error | Test expression in Python REPL first: `python -c "AGE='34'; print(int(AGE or 0) > 18)"` |
| `[extract] 0 rows` after filter | Filter too strict | Relax condition; check string vs numeric: `"34" > 18` is False in Python |
| `[extract] 0 rows` after auto-detect probe | Wrong sheet probed — `--sheet` omitted | Multi-sheet files: always include `--sheet <name>` in the probe command. Without `--sheet`, the extractor probes the *first* sheet (often a cover/instructions tab), finds "headers" there, and returns 0 matches on the real data sheet. |
| Wrong rows returned — data looks like it's from the wrong sheet | Sheet not specified / wrong sheet selected | Discover available sheets: run with `--sheet _dummy_` to print `Available sheets: ...`. Skip sheets with `_` prefix (metadata). Pick the sheet name that best matches the user's task. |
| Empty JSON array `[]` | Sheet has no data rows (header only) | Correct — sheet is empty |

---

## Viewer Server Errors

These are local viewer issues surfaced through `extract.py --view` or `python -m scripts view ...`.

| Symptom | Cause | Fix |
|---|---|---|
| `ValueError: Sheet index 0 out of range` | xlsx has zero sheets | File corrupt or not a real xlsx |
| `ValueError: Sheet 'X' not found. Available: ...` | `--sheet` name wrong | Copy exact name from "Available:" list |
| `zipfile.BadZipFile` | File not a real xlsx (e.g., renamed .xls) | Open in Excel, Save As → `.xlsx` |
| `.xls` file rejected | Old binary format, no stdlib parser | Save as `.xlsx` in Excel: File → Save As → Excel Workbook (.xlsx) |
| Server starts but `/data` returns `{"sheets":null,"data":{"":[]}}` | CSV file is empty or header-only | Check source file: `head data.csv` |
| `OSError: [Errno 98] Address already in use` | Port collision | Use `--port 0` or choose different port |
| Viewer loads but table blank | JSON parse failure | Check browser console for JS error; verify `/data` returns valid JSON |
| `UnicodeDecodeError` on CSV | Wrong encoding | Re-export the CSV as UTF-8 (for example from Excel) and retry |

---

## Browser / Chrome DevTools MCP Errors

| Symptom | Cause | Fix |
|---|---|---|
| "browser already running for chrome-profile" | DevTools MCP locked to existing session | Use `curl /data` instead — no browser needed |
| `wait_for(selector="table tbody tr")` times out | Data not loaded yet | Increase wait timeout; check if server responded to `/data` first |
| Filter input not found | Wrong selector | Use `document.getElementById('filter-input')` not CSS class |
| Tab click has no effect | Sheet tab not rendered (single-sheet CSV) | No tabs for CSV or single-sheet xlsx; table is already showing correct data |
| `evaluate_script` returns `null` for `VIEW` | Filter not yet applied | Click Apply button first; wait for obs count to update |
| Export download not captured by agent | Browser download goes to disk | Don't use export button for agent pipelines — use `curl /data` + filter in Python |

---

## Platform-Specific

| Platform | Symptom | Fix |
|---|---|---|
| Windows | `python: command not found` | Use `py` or `py -3` instead of `python`; Microsoft Store Python alias may be active |
| Windows | `kill %1` fails | Use `taskkill /PID <pid> /F` or track PID and use `proc.terminate()` in Python |
| macOS | `python` is Python 2 | Use `python3` explicitly |
| GitHub Actions / CI | Server starts but port unreachable | Ensure no firewall rule blocks localhost; use `127.0.0.1` not `localhost` |
| Codespaces | Port not forwarded | Codespaces auto-forwards; use the forwarded URL shown in Ports tab |

---

## Data Quality Issues

| Symptom | Cause | Fix |
|---|---|---|
| Numeric column sorts as string | Values are strings by default | Cast in filter: `int(AGE or 0)` |
| Missing values not showing as `.` | Only browser viewer shows `.` indicator | In JSON output, missing = `""` (empty string) |
| Column count wrong | xlsx has merged header cells | Merged cells not supported; unmerge in Excel first |
| Column names duplicated | xlsx sheet has duplicate headers | Later duplicates are suffixed as ` [2]`, ` [3]` — use the exact modified name in filters, or prefer `_col` indices |
| Encoded characters garbled | Encoding mismatch on CSV | Try `--encoding utf-8-sig` (BOM), `latin-1`, or `cp1252` |
| Shared string lookup blank | Corrupt xlsx sharedStrings.xml | Re-export xlsx from source application |

---

## Debugging Checklist

1. Can Python find the script?
   ```bash
   python -m scripts view --help
   ```

2. Can the server start and serve `/data`?
   ```bash
   python -m scripts view data.xlsx --port 8765 --no-open &
   sleep 2 && curl -s http://127.0.0.1:8765/data | python -m json.tool | head -20
   kill %1
   ```

3. Does `extract.py` work headless?
   ```bash
   python extract.py data.xlsx 2>&1 | head -5
   ```

4. Does filter expression work standalone?
   ```bash
   python -c "AGE='34'; SEX='F'; print(int(AGE or 0) > 18 and SEX == 'F')"
   ```
