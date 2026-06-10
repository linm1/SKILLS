#!/usr/bin/env python3
"""
tabview-to-json extractor — standalone CLI wrapper around csvseljson.py.

No browser required. Starts the viewer server, fetches /data, applies an
optional Python-side filter expression, writes JSON output.

Usage
-----
  python extract.py input.csv
  python extract.py input.xlsx
  python extract.py input.xlsx --sheet ADSL
  python extract.py input.xlsx --sheet ADSL --where "AGE > 50 and SEX == 'F'"
  python extract.py input.xlsx --out records.json
  python extract.py input.xlsx --sheet ADSL --cols USUBJID AGE SEX ARM

Where expression
----------------
  Standard Python boolean expression. Column names used as variables.
  All values arrive as strings — cast explicitly: int(AGE) > 50
  Missing values are empty strings: SEX != ""

  Examples:
    "AGE > '50'"                           # string compare (works if all numeric)
    "int(AGE or 0) > 50 and SEX == 'F'"   # safe numeric cast
    "ARM in ('Placebo', 'Treatment A')"    # set membership
    "USUBJID.startswith('001')"            # string method

Exit codes
----------
  0  success
  1  file not found / sheet not found
  2  server failed to start
  3  filter expression error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
CSVSELJSON = SCRIPT_DIR / "csvseljson.py"


_MISSING_SHEET_RE = re.compile(
    r"ValueError:\s+Sheet '(?P<sheet>[^']+)' not found\. Available:\s*(?P<available>.+)"
)


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(
    port: int,
    proc: subprocess.Popen[str] | None = None,
    timeout: float = 10.0,
) -> tuple[bool, bool]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            return False, True
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/data", timeout=1)
            return True, False
        except Exception:
            time.sleep(0.2)
    return False, proc is not None and proc.poll() is not None


def _fetch_data(port: int) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/data", timeout=15) as r:
        return json.loads(r.read())


def _parse_missing_sheet_error(stderr: str) -> tuple[str, str] | None:
    for line in reversed(stderr.splitlines()):
        match = _MISSING_SHEET_RE.search(line.strip())
        if match:
            return match.group("sheet"), match.group("available").strip()
    return None


def _translate_sas_where(expr: str) -> str:
    """Translate SAS WHERE syntax to Python boolean expression (pure, no side effects)."""
    result = expr

    # Strip leading WHERE keyword
    result = re.sub(r"^\s*WHERE\s+", "", result, flags=re.IGNORECASE)

    # NOT IN before IN (order matters)
    result = re.sub(r"\bNOT\s+IN\b", "not in", result, flags=re.IGNORECASE)

    # IN keyword (standalone, not part of "not in" already translated)
    result = re.sub(r"(?<!not\s)\bIN\b", "in", result, flags=re.IGNORECASE)

    # CONTAINS: COL CONTAINS 'x' -> 'x' in COL
    result = re.sub(
        r"(\w+)\s+CONTAINS\s+('[^']*'|\"[^\"]*\")",
        lambda m: f"{m.group(2)} in {m.group(1)}",
        result,
        flags=re.IGNORECASE,
    )

    # ^= -> !=
    result = re.sub(r"\^=", "!=", result)

    # NE keyword -> !=
    result = re.sub(r"\bNE\b", "!=", result, flags=re.IGNORECASE)

    # Bare = -> == (but not <=, >=, !=, ^= which are already handled).
    # Split on quoted tokens so that = inside string literals is not touched.
    def _replace_bare_eq_outside_strings(s: str) -> str:
        parts = re.split(r"('[^']*'|\"[^\"]*\")", s)
        result_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 1:  # inside a quoted literal — leave untouched
                result_parts.append(part)
            else:
                result_parts.append(re.sub(r"(?<![<>!=])=(?!=)", "==", part))
        return "".join(result_parts)

    result = _replace_bare_eq_outside_strings(result)

    # AND/OR keywords
    result = re.sub(r"\bAND\b", "and", result, flags=re.IGNORECASE)
    result = re.sub(r"\bOR\b", "or", result, flags=re.IGNORECASE)

    # NOT keyword (standalone, not part of "not in")
    result = re.sub(r"\bNOT\b(?!\s+in\b)", "not", result, flags=re.IGNORECASE)

    return result


def _apply_where(rows: list[dict], expr: str) -> list[dict]:
    """Filter rows using a Python boolean expression. Column values injected as locals."""
    translated = _translate_sas_where(expr)
    if translated != expr:
        print(f"[extract] SAS→Python: {translated}", file=sys.stderr)

    safe_builtins = {"float": float, "int": int, "str": str, "bool": bool, "len": len, "abs": abs, "round": round}

    # Pre-check: compile the translated expression once before iterating rows.
    # Fail fast with a clear message if the expression has a syntax error.
    try:
        compile(translated, "<where>", "eval")
        expr_to_use = translated
    except SyntaxError as e:
        print(f"[extract] --where expression has a syntax error (after SAS translation): {e}", file=sys.stderr)
        print(f"[extract] Translated form was: {translated}", file=sys.stderr)
        sys.exit(3)

    out = []
    for row in rows:
        try:
            # Build a flat namespace from the row — column names become variables
            # Also expose `row` itself so callers can use row.get(col, default)
            ns = dict(row)
            ns["row"] = row
            result = eval(expr_to_use, {"__builtins__": safe_builtins}, ns)  # noqa: S307 — controlled eval
            if result:
                out.append(row)
        except Exception as e:
            print(f"[extract] filter error on row {row}: {e}", file=sys.stderr)
            sys.exit(3)
    return out


def _resolve_cols(cols: list[str], keys: list[str]) -> list[str]:
    resolved = []
    for c in cols:
        try:
            idx = int(c)
            if idx < 0:
                raise ValueError("negative column index")
            resolved.append(keys[idx])
        except (ValueError, IndexError):
            resolved.append(c)
    return resolved


def _select_cols(rows: list[dict], cols: list[str]) -> list[dict]:
    if not rows:
        return rows
    keys = list(rows[0].keys())
    resolved = _resolve_cols(cols, keys)
    known = set(rows[0].keys())
    unknown = [c for c in resolved if c not in known]
    if unknown:
        print(f"[extract] --cols: unknown column(s) (will be empty): {unknown}", file=sys.stderr)
    return [{c: r.get(c, "") for c in resolved} for r in rows]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extract records from CSV/xlsx/xlsm via csvseljson viewer → JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("file", help="Input .csv, .xlsx, or .xlsm file")
    ap.add_argument("--sheet", default=None, help="Sheet name or 0-based index (xlsx/xlsm only)")
    ap.add_argument("--where", default=None, metavar="EXPR",
                    help="Python boolean filter expression (column names as variables)")
    ap.add_argument("--cols", nargs="+", metavar="COL", help="Output only these columns")
    ap.add_argument("--out", default=None, metavar="FILE", help="Output JSON file (default: stdout)")
    ap.add_argument("--indent", type=int, default=2, help="JSON indent (default: 2; 0 = compact)")
    ap.add_argument("--limit", type=int, default=None, metavar="N",
                    help="Stop after N records (useful for column discovery)")
    ap.add_argument("--port", type=int, default=0, help="Server port (0 = auto-detect free port)")
    hdr_group = ap.add_mutually_exclusive_group()
    hdr_group.add_argument("--raw-top", type=float, default=None, metavar="PCT",
                           help="Return first PCT%% of rows as raw arrays (no header detection); min 10 rows.")
    hdr_group.add_argument("--header-row", type=int, default=None, metavar="N",
                           help="Use row N (1-based) as header, bypassing auto-detection.")
    ap.add_argument("--view", action="store_true",
                    help="After extraction, open result.json in the localhost viewer (requires --out)")
    args = ap.parse_args()

    if args.view and not args.out:
        print("[extract] --view requires --out <file>", file=sys.stderr)
        sys.exit(3)

    # Validate input
    input_path = Path(args.file)
    if not input_path.exists():
        print(f"[extract] File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not CSVSELJSON.exists():
        print(f"[extract] csvseljson.py not found at {CSVSELJSON}", file=sys.stderr)
        print("[extract] Place csvseljson.py next to extract.py", file=sys.stderr)
        sys.exit(1)

    # Pick port
    port = args.port if args.port else _find_free_port()

    # Build command
    cmd = [sys.executable, str(CSVSELJSON), "view", str(input_path),
           "--port", str(port), "--no-open"]
    if args.sheet is not None:
        cmd += ["--sheet", args.sheet]
    if args.raw_top is not None:
        cmd += ["--raw-top", str(args.raw_top)]
    if args.header_row is not None:
        cmd += ["--header-row", str(args.header_row)]
    # Start server
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        started, worker_exited = _wait_for_server(port, proc=proc, timeout=15)
        if not started:
            stderr = proc.stderr.read() if proc.stderr else ""
            if worker_exited:
                missing_sheet = _parse_missing_sheet_error(stderr)
                if missing_sheet is not None:
                    missing_name, available = missing_sheet
                    if args.sheet == "_dummy_" and missing_name == "_dummy_":
                        print(f"Available sheets: {available}")
                        return
                    print(f"[extract] Sheet '{missing_name}' not found.", file=sys.stderr)
                    print(f"[extract] Available: {available}", file=sys.stderr)
                    sys.exit(1)
                print(
                    "[extract] Extractor worker exited before the local data server became ready.",
                    file=sys.stderr,
                )
                if stderr:
                    print(stderr, file=sys.stderr)
                sys.exit(proc.returncode if proc.returncode else 2)
            print(f"[extract] Server failed to start on port {port}", file=sys.stderr)
            if stderr:
                print(stderr, file=sys.stderr)
            sys.exit(2)

        # Fetch data
        payload = _fetch_data(port)

        # Raw probe mode: server set __raw__ sentinel — output raw rows directly.
        # Skip sheet resolution, --where, --cols, --limit (meaningless without a header).
        data = payload.get("data", {})
        if data.get("__raw__"):
            raw_rows = [v for k, v in data.items() if k != "__raw__"]
            # Flatten: each value is the raw list for a sheet (usually one sheet)
            flat: list = []
            for sheet_rows in raw_rows:
                if isinstance(sheet_rows, list):
                    flat.extend(sheet_rows)
            indent = args.indent if args.indent > 0 else None
            output = json.dumps(flat, indent=indent, ensure_ascii=False)
            if args.out:
                out_path = Path(args.out)
                out_path.write_text(output, encoding="utf-8")
                print(f"[extract] raw probe: {len(flat)} rows → {out_path}", file=sys.stderr)
            else:
                print(output)
            return

        # Resolve sheet
        sheets = payload.get("sheets")

        if sheets is None:
            # CSV uses key ""; xlsx with single --sheet uses the sheet name as key
            if "" in data:
                target_rows = data[""]
            else:
                target_rows = next(iter(data.values()), [])
            sheet_label = next(iter(data.keys()), "data") or "data"
        elif args.sheet is not None:
            # User specified a sheet — find it
            sheet_name = None
            # Try numeric index
            try:
                idx = int(args.sheet)
                sheet_name = sheets[idx]
            except (ValueError, IndexError):
                pass
            if sheet_name is None and args.sheet in data:
                sheet_name = args.sheet
            if sheet_name is None:
                print(f"[extract] Sheet '{args.sheet}' not found.", file=sys.stderr)
                print(f"[extract] Available: {', '.join(sheets)}", file=sys.stderr)
                sys.exit(1)
            target_rows = data[sheet_name]
            sheet_label = sheet_name
        else:
            # No sheet specified — first sheet
            sheet_name = sheets[0]
            target_rows = data[sheet_name]
            sheet_label = sheet_name

        # Apply limit (before filter for discovery, semantically "first N rows")
        if args.limit is not None:
            target_rows = target_rows[: args.limit]

        # Apply WHERE filter
        if args.where:
            before = len(target_rows)
            target_rows = _apply_where(target_rows, args.where)
            print(f"[extract] Filter: {before} → {len(target_rows)} rows", file=sys.stderr)

        # Select columns
        if args.cols:
            target_rows = _select_cols(target_rows, args.cols)

        # Serialize
        indent = args.indent if args.indent > 0 else None
        output = json.dumps(target_rows, indent=indent, ensure_ascii=False)

        # Write
        if args.out:
            out_path = Path(args.out)
            out_path.write_text(output, encoding="utf-8")
            col_info = f"{len(target_rows[0])} cols" if target_rows else "0 cols"
            print(f"[extract] {sheet_label}: {len(target_rows)} rows, {col_info} → {out_path}",
                  file=sys.stderr)
        else:
            print(output)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

    # Open viewer after server is fully stopped
    if args.view and args.out:
        view_port = _find_free_port()
        url = f"http://127.0.0.1:{view_port}/"
        print(f"\n[extract] Opening viewer at {url}", file=sys.stderr)
        print("[extract] Press Ctrl+C to stop.", file=sys.stderr)
        subprocess.run(
            [sys.executable, str(CSVSELJSON), "view", str(Path(args.out).resolve()),
             "--port", str(view_port)],
            check=False,
        )


if __name__ == "__main__":
    main()
