#!/usr/bin/env python3
"""csvseljson: serve tabular data through a minimal browser viewer.

View tabular files
    python csvseljson.py view data.json
    python csvseljson.py view data.xlsx --port 0

Viewer features (minimum)
- Render JSON array of objects as a table
- SAS-style formula filter (case-insensitive, including strings)
- Jump to column
- Click-to-sort (numeric supports comma thousands separators)

Dependencies
- Standard library only; optional orjson for faster JSON serialization.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Sequence

try:
    import orjson  # type: ignore
except Exception:  # pragma: no cover
    orjson = None


def _dumps(obj) -> bytes:
    if orjson is not None:
        return orjson.dumps(obj)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _col_letter_to_idx(col: str) -> int:
    """Convert Excel column letters (A, B, ..., Z, AA, AB, ...) to 0-based index."""
    idx = 0
    for ch in col.upper():
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1


def _is_numeric(s: str) -> bool:
    """Return True if string represents a valid number. Empty strings return False."""
    if not isinstance(s, str):
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def _dedupe_headers(headers: Sequence[str]) -> List[str]:
    """Preserve duplicate header columns by suffixing later occurrences.

    The first occurrence keeps its original name so existing filters like
    row.get('QC Programmer(s)', '') still work. Later duplicates get a
    stable " [2]", " [3]", ... suffix.
    """
    counts: Dict[str, int] = {}
    unique: List[str] = []
    for header in headers:
        count = counts.get(header, 0) + 1
        counts[header] = count
        unique.append(header if count == 1 else f"{header} [{count}]")
    return unique


def _looks_like_header(
    flat: list,
    min_cols: int = 6,
    min_dense_cols: int = 5,
    min_density: float = 0.6,
    max_cell_len: int = 40,
) -> bool:
    """Return True if row looks like a column header row.

    A header row has either:
    - >= min_cols non-empty short strings, or
    - a dense 5-column-style row where nearly every visible cell is a short string.

    None values are ignored. Preamble rows (titles, key-value pairs, sparse group
    labels) typically have too few populated cells or too much empty span.
    """
    short_strings = []
    populated = 0
    first_nonempty = None
    last_nonempty = None
    for idx, v in enumerate(flat):
        if v is None:
            continue
        cell_str = str(v).strip()
        if not cell_str:
            continue
        populated += 1
        if first_nonempty is None:
            first_nonempty = idx
        last_nonempty = idx
        if len(cell_str) <= max_cell_len and not _is_numeric(cell_str):
            short_strings.append(cell_str)

    short_count = len(short_strings)
    if short_count >= min_cols:
        return True
    if short_count < min_dense_cols or first_nonempty is None or last_nonempty is None:
        return False

    visible_span = last_nonempty - first_nonempty + 1
    return populated == short_count and visible_span > 0 and (short_count / visible_span) >= min_density


def parse_xlsx(
    path: str,
    sheet: Optional[str] = None,
    raw_top: Optional[float] = None,
    header_row: Optional[int] = None,
) -> "Dict[str, List[Dict]]":
    """Parse an xlsx file using stdlib only. Returns dict {sheet_name: [row_dict, ...]}.

    raw_top: if set, return the first PCT% of rows as raw arrays (no header detection),
             min 10 rows. Top-level '__raw__' key is set to True in the result.
    header_row: if set, use row N (1-based) as header, skip heuristic entirely.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    NS = {
        'wb': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r':  'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'rel':'http://schemas.openxmlformats.org/package/2006/relationships',
    }

    def _text(el):
        return ''.join(el.itertext()) if el is not None else ''

    try:
        zf = zipfile.ZipFile(path, 'r')
    except zipfile.BadZipFile:
        raise ValueError(f"Not a valid xlsx file: {path}")

    with zf:
        names = zf.namelist()

        # 1. Shared strings
        shared: List[str] = []
        if 'xl/sharedStrings.xml' in names:
            root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
            for si in root:
                t_el = si.find('wb:t', NS)
                if t_el is None:
                    parts = [_text(r.find('wb:t', NS)) for r in si.findall('wb:r', NS)]
                    shared.append(''.join(p for p in parts if p is not None))
                else:
                    shared.append(t_el.text or '')

        # 2. Workbook: sheet names + rIds
        wb_root = ET.fromstring(zf.read('xl/workbook.xml'))
        sheet_nodes = wb_root.findall('.//wb:sheet', NS)
        sheet_order = [(s.get('name', ''), s.get('{%s}id' % NS['r'], '')) for s in sheet_nodes]

        # 3. Relationships: rId -> filename
        rels_root = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
        rid_to_file: Dict[str, str] = {}
        for rel in rels_root:
            target = rel.get('Target', '')
            # Target may be absolute (/xl/worksheets/sheet1.xml) or relative (worksheets/sheet1.xml)
            stripped = target.lstrip('/')
            fname = stripped if stripped.startswith('xl/') else 'xl/' + stripped
            rid_to_file[rel.get('Id', '')] = fname

        # 4. Resolve --sheet filter
        available = [name for name, _ in sheet_order]
        targets: List[tuple] = []
        if sheet is not None:
            try:
                idx = int(sheet)
            except (ValueError, TypeError):
                idx = None
            if idx is not None:
                if idx < 0 or idx >= len(sheet_order):
                    raise ValueError(
                        f"Sheet index {idx} out of range. Available sheets (0-based): "
                        + ', '.join(f"{i}: {n}" for i, (n, _) in enumerate(sheet_order))
                    )
                targets = [sheet_order[idx]]
            else:
                match = [(n, r) for n, r in sheet_order if n == sheet]
                if not match:
                    raise ValueError(
                        f"Sheet '{sheet}' not found. Available: {', '.join(available)}"
                    )
                targets = match
        else:
            targets = sheet_order

        # 5. Parse each target sheet
        result: Dict[str, List[Dict]] = {}
        for sheet_name, rid in targets:
            fname = rid_to_file.get(rid, '')
            if not fname or fname not in names:
                result[sheet_name] = []
                continue

            ws_root = ET.fromstring(zf.read(fname))
            rows_el = ws_root.findall('.//wb:sheetData/wb:row', NS)

            def _sheet_row_number(row_el, fallback: int) -> int:
                raw_num = row_el.get('r')
                if raw_num is None:
                    return fallback
                try:
                    return int(raw_num)
                except ValueError:
                    return fallback

            def _extract_flat(row_el) -> List:
                """Extract cell values from a row element into a flat list."""
                cells = row_el.findall('wb:c', NS)
                row_vals: Dict[int, str] = {}
                for c_el in cells:
                    ref = c_el.get('r', '')
                    col_str = ''.join(ch for ch in ref if ch.isalpha())
                    if not col_str:
                        continue
                    col_idx = _col_letter_to_idx(col_str)
                    t = c_el.get('t', '')
                    v_el = c_el.find('wb:v', NS)
                    is_el = c_el.find('wb:is', NS)
                    if t == 's':
                        raw_idx = int(v_el.text) if v_el is not None and v_el.text else 0
                        val = shared[raw_idx] if raw_idx < len(shared) else ''
                    elif t == 'inlineStr':
                        val = _text(is_el.find('wb:t', NS)) if is_el is not None else ''
                    elif t == 'b':
                        val = '1' if (v_el is not None and v_el.text == '1') else '0'
                    else:
                        val = v_el.text if v_el is not None else ''
                    row_vals[col_idx] = val
                if not row_vals:
                    return []
                max_idx = max(row_vals.keys())
                return [row_vals.get(i, '') for i in range(max_idx + 1)]

            # --- RAW-TOP MODE ---
            if raw_top is not None:
                # Preserve actual 1-based sheet row numbers before filtering empties.
                numbered = [
                    (_sheet_row_number(row_el, i + 1), _extract_flat(row_el))
                    for i, row_el in enumerate(rows_el)
                ]
                numbered = [(rn, f) for rn, f in numbered if f]  # drop empty rows
                n = max(int(len(numbered) * raw_top / 100), 10)
                raw_rows = [{"_row": rn, "_col": list(range(len(cells))), "_cells": cells} for rn, cells in numbered[:n]]
                result[sheet_name] = raw_rows
                continue  # skip to next sheet

            header: List[str] = []
            header_found: bool = False
            data_rows: List[Dict] = []

            for fallback_row_num, row_el in enumerate(rows_el, start=1):
                row_num = _sheet_row_number(row_el, fallback_row_num)
                flat = _extract_flat(row_el)

                if not flat:
                    continue

                if header_row is not None:
                    # Explicit header row mode — skip heuristic
                    if row_num < header_row:
                        continue  # discard preamble
                    elif row_num == header_row:
                        header = _dedupe_headers([str(v) for v in flat])
                        header_found = True
                    else:
                        rec = {h: (flat[j] if j < len(flat) else '') for j, h in enumerate(header)}
                        data_rows.append(rec)
                else:
                    # Auto-detect heuristic path
                    if not header_found:
                        if _looks_like_header(flat):
                            header = _dedupe_headers([str(v) for v in flat])
                            header_found = True
                        # else: skip preamble row — header not yet found
                    else:
                        rec = {}
                        for i, h in enumerate(header):
                            rec[h] = flat[i] if i < len(flat) else ''
                        data_rows.append(rec)

            # If header was never detected, data_rows is empty — intentional.
            # Use --raw-top to probe the file and identify the header row first.
            result[sheet_name] = data_rows

        if raw_top is not None:
            result["__raw__"] = True  # sentinel: raw probe output, not tabular data

    return result


_VIEW_HTML = '<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1" />\n  <title>csvseljson viewer</title>\n  <style>\n    :root { color-scheme: light; }\n    body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }\n    .bar { position: sticky; top: 0; z-index: 3; background: #fff; border-bottom: 1px solid #ddd; padding: 8px 10px; display: grid; gap: 6px; }\n    .row { display: grid; grid-template-columns: 1fr auto auto; gap: 6px; align-items: center; }\n    #formula { width: 100%; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; padding: 6px 8px; border: 1px solid #bbb; box-sizing: border-box; }\n    #formula.active { border-color: #e07b00; box-shadow: 0 0 0 2px #e07b0033; }\n    button { padding: 6px 10px; border: 1px solid #bbb; background: #f7f7f7; cursor: pointer; font-size: 13px; white-space: nowrap; }\n    button:hover { background: #eee; }\n    .status { font-size: 12px; color: #555; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }\n    .err { color: #fff; background: #b00020; padding: 2px 8px; border-radius: 3px; white-space: pre-wrap; display: none; }\n    .err.show { display: inline; }\n    .nav { display: grid; grid-template-columns: 1fr auto; gap: 6px; align-items: center; }\n    input[type=text] { width: 100%; padding: 6px 8px; border: 1px solid #bbb; font-size: 13px; box-sizing: border-box; }\n    .wrap { height: calc(100vh - var(--bar-h, 110px)); overflow: auto; }\n    table { border-collapse: collapse; width: max-content; min-width: 100%; }\n    thead th { position: sticky; top: 0; z-index: 2; background: #f0f0f0; border-bottom: 2px solid #ccc; cursor: pointer; user-select: none; white-space: nowrap; text-align: left; }\n    th, td { border-right: 1px solid #e0e0e0; border-bottom: 1px solid #e0e0e0; padding: 4px 8px; font-size: 12px; white-space: nowrap; }\n    td:not(.obs) { white-space: normal; word-break: break-word; max-width: 60ch; }\n    td.obs { color: #888; text-align: right; font-variant-numeric: tabular-nums; background: #fafafa; position: sticky; left: 0; z-index: 1; border-right: 1px solid #ccc; }\n    th.obs { position: sticky; left: 0; z-index: 3; background: #f0f0f0; }\n    td[data-missing] { color: #aaa; font-style: italic; }\n    tr:nth-child(even) td { background: #f9f9f9; }\n    tr:nth-child(even) td.obs { background: #f3f3f3; }\n    tr:hover td { background: #eef4ff; }\n    tr:hover td.obs { background: #e4ecf8; }\n    .hl { outline: 2px solid #2b78ff; outline-offset: -2px; }\n    .sort-arrow { font-size: 10px; margin-left: 4px; color: #2b78ff; }\n    .muted { color: #888; }\n    .tabs { display: flex; gap: 0; border-bottom: 2px solid #ccc; background: #f5f5f5; overflow-x: auto; flex-shrink: 0; }\n    .tab { padding: 6px 16px; font-size: 12px; cursor: pointer; border: 1px solid transparent; border-bottom: none; white-space: nowrap; color: #555; background: #f5f5f5; }\n    .tab:hover { background: #ececec; }\n    .tab.active { background: #fff; border-color: #ccc; border-bottom-color: #fff; margin-bottom: -2px; color: #111; font-weight: 600; }\n    .export-btns { display: flex; gap: 4px; margin-left: auto; }\n  </style>\n</head>\n<body>\n  <div id="tabbar" class="tabs" style="display:none"></div>\n  <div class="bar" id="bar">\n    <div class="row">\n      <input id="formula" type="text" placeholder=\'WHERE e.g. dataset = "ADSL" and age > 18  (Ctrl+Enter to apply)\' />\n      <button id="apply">Apply</button>\n      <button id="clear">Clear</button>\n      <span class="export-btns"><button id="expjson">&#8595;&#160;JSON</button><button id="expcsv">&#8595;&#160;CSV</button></span>\n    </div>\n    <div class="nav">\n      <input id="coljump" type="text" list="colnames" placeholder=\'Jump to column — spaces: ["Display Format"]\' />\n      <button id="jump">Jump</button>\n      <datalist id="colnames"></datalist>\n    </div>\n    <div class="status">\n      <span id="count" class="muted">Loading\u2026</span>\n      <span id="err" class="err"></span>\n    </div>\n  </div>\n\n  <div class="wrap" id="wrap">\n    <table id="tbl">\n      <thead id="thead"></thead>\n      <tbody id="tbody"></tbody>\n    </table>\n  </div>\n\n<script>\n\'use strict\';\n\nfunction isMissing(v) {\n  if (v === null || v === undefined) return true;\n  if (typeof v === \'string\') return v.trim().length === 0;\n  return false;\n}\n\nconst numRe = /^[-+]?((\\d{1,3}(,\\d{3})+)|\\d+)(\\.\\d+)?([eE][-+]?\\d+)?$/;\nfunction parseNum(v) {\n  if (v === null || v === undefined) return null;\n  if (typeof v === \'number\') return Number.isFinite(v) ? v : null;\n  const s = String(v).trim();\n  if (!s) return null;\n  if (!numRe.test(s)) return null;\n  const cleaned = s.replace(/,/g, \'\');\n  const n = Number(cleaned);\n  return Number.isFinite(n) ? n : null;\n}\n\nfunction ci(s) { return String(s ?? \'\').toLowerCase(); }\n\nfunction cmpValues(a, b) {\n  const na = parseNum(a);\n  const nb = parseNum(b);\n  if (na !== null && nb !== null) {\n    if (na < nb) return -1;\n    if (na > nb) return 1;\n    return 0;\n  }\n  const sa = ci(isMissing(a) ? \'\' : a);\n  const sb = ci(isMissing(b) ? \'\' : b);\n  if (sa < sb) return -1;\n  if (sa > sb) return 1;\n  return 0;\n}\n\n// Token types: IDENT, STRING, NUMBER, OP, LP, RP, LBR, RBR, COMMA, EOF\nfunction tokenize(input) {\n  const s = input;\n  const tokens = [];\n  let i = 0;\n\n  const isAlpha = c => /[A-Za-z_]/.test(c);\n  const isAlnum = c => /[A-Za-z0-9_]/.test(c);\n  const isDigit = c => /[0-9]/.test(c);\n\n  while (i < s.length) {\n    const c = s[i];\n    if (c === \' \' || c === \'\\t\' || c === \'\\n\' || c === \'\\r\') { i++; continue; }\n\n    if (c === \'(\') { tokens.push({t:\'LP\', v:c}); i++; continue; }\n    if (c === \')\') { tokens.push({t:\'RP\', v:c}); i++; continue; }\n    if (c === \'[\') { tokens.push({t:\'LBR\', v:c}); i++; continue; }\n    if (c === \']\') { tokens.push({t:\'RBR\', v:c}); i++; continue; }\n    if (c === \',\') { tokens.push({t:\'COMMA\', v:c}); i++; continue; }\n\n    if (c === \'<\' || c === \'>\' || c === \'=\' || c === \'^\') {\n      let op = c;\n      if ((c === \'<\' || c === \'>\') && s[i+1] === \'=\') { op += \'=\'; i += 2; tokens.push({t:\'OP\', v:op}); continue; }\n      if (c === \'^\' && s[i+1] === \'=\') { op = \'^=\'; i += 2; tokens.push({t:\'OP\', v:op}); continue; }\n      if (c === \'=\' || c === \'<\' || c === \'>\') { i++; tokens.push({t:\'OP\', v:op}); continue; }\n    }\n\n    if (c === \'"\' || c === "\'") {\n      const q = c;\n      i++;\n      let out = \'\';\n      while (i < s.length) {\n        const ch = s[i];\n        if (ch === \'\\\\\') {\n          const nxt = s[i+1];\n          if (nxt === undefined) break;\n          out += nxt;\n          i += 2;\n          continue;\n        }\n        if (ch === q) { i++; break; }\n        out += ch;\n        i++;\n      }\n      tokens.push({t:\'STRING\', v:out});\n      continue;\n    }\n\n    if (isDigit(c) || ((c === \'+\' || c === \'-\') && isDigit(s[i+1] || \'\'))) {\n      let j = i;\n      while (j < s.length && /[0-9+\\-.,eE]/.test(s[j])) j++;\n      const raw = s.slice(i, j);\n      const rawTrim = raw.trim();\n      if (numRe.test(rawTrim)) {\n        tokens.push({t:\'NUMBER\', v:rawTrim});\n        i = j;\n        continue;\n      }\n    }\n\n    if (isAlpha(c)) {\n      let j = i + 1;\n      while (j < s.length && isAlnum(s[j])) j++;\n      const ident = s.slice(i, j);\n      tokens.push({t:\'IDENT\', v:ident});\n      i = j;\n      continue;\n    }\n\n    throw new Error(`Unexpected character \'${c}\' at position ${i}`);\n  }\n\n  tokens.push({t:\'EOF\', v:\'\'});\n  return tokens;\n}\n\nfunction Parser(tokens) { this.tokens = tokens; this.pos = 0; }\nParser.prototype.peek = function() { return this.tokens[this.pos]; };\nParser.prototype.next = function() { return this.tokens[this.pos++]; };\nParser.prototype.expect = function(type) {\n  const tok = this.next();\n  if (tok.t !== type) throw new Error(`Expected ${type} but got ${tok.t}`);\n  return tok;\n};\n\nParser.prototype.parse = function() {\n  const node = this.orExpr();\n  if (this.peek().t !== \'EOF\') throw new Error(`Unexpected token \'${this.peek().v}\'`);\n  return node;\n};\n\nParser.prototype.orExpr = function() {\n  let left = this.andExpr();\n  while (this.peek().t === \'IDENT\' && ci(this.peek().v) === \'or\') {\n    this.next();\n    const right = this.andExpr();\n    left = {k:\'or\', a:left, b:right};\n  }\n  return left;\n};\n\nParser.prototype.andExpr = function() {\n  let left = this.notExpr();\n  while (this.peek().t === \'IDENT\' && ci(this.peek().v) === \'and\') {\n    this.next();\n    const right = this.notExpr();\n    left = {k:\'and\', a:left, b:right};\n  }\n  return left;\n};\n\nParser.prototype.notExpr = function() {\n  if (this.peek().t === \'IDENT\' && ci(this.peek().v) === \'not\') {\n    this.next();\n    const inner = this.notExpr();\n    return {k:\'not\', a:inner};\n  }\n  return this.compExpr();\n};\n\nParser.prototype.compExpr = function() {\n  let left = this.term();\n  const tok = this.peek();\n  if (tok.t === \'OP\' || (tok.t === \'IDENT\' && ci(tok.v) === \'ne\')) {\n    const opTok = this.next();\n    const op = (opTok.t === \'IDENT\') ? ci(opTok.v) : opTok.v;\n    const right = this.term();\n    return {k:\'cmp\', op:op, a:left, b:right};\n  }\n  return left;\n};\n\nParser.prototype.term = function() {\n  const tok = this.peek();\n  if (tok.t === \'LP\') {\n    this.next();\n    const inner = this.orExpr();\n    this.expect(\'RP\');\n    return inner;\n  }\n  if (tok.t === \'LBR\') {\n    this.next();\n    const s = this.expect(\'STRING\').v;\n    this.expect(\'RBR\');\n    return {k:\'col\', name:s};\n  }\n  if (tok.t === \'STRING\') { this.next(); return {k:\'str\', v:tok.v}; }\n  if (tok.t === \'NUMBER\') { this.next(); return {k:\'num\', v:tok.v}; }\n\n  if (tok.t === \'IDENT\') {\n    const name = tok.v;\n    this.next();\n    if (this.peek().t === \'LP\') {\n      this.next();\n      const args = [];\n      if (this.peek().t !== \'RP\') {\n        args.push(this.orExpr());\n        while (this.peek().t === \'COMMA\') { this.next(); args.push(this.orExpr()); }\n      }\n      this.expect(\'RP\');\n      return {k:\'call\', name:name, args:args};\n    }\n    return {k:\'col\', name:name};\n  }\n\n  throw new Error(`Unexpected token \'${tok.v || tok.t}\'`);\n};\n\nfunction buildColMap(columns) {\n  const map = new Map();\n  for (const col of columns) {\n    const key = ci(col);\n    if (!map.has(key)) map.set(key, col);\n  }\n  return map;\n}\n\nfunction getCell(row, colName, colMap) {\n  const real = colMap.get(ci(colName));\n  if (!real) return undefined;\n  return row[real];\n}\n\nfunction evalNode(node, row, colMap) {\n  switch (node.k) {\n    case \'or\': return Boolean(evalNode(node.a, row, colMap)) || Boolean(evalNode(node.b, row, colMap));\n    case \'and\': return Boolean(evalNode(node.a, row, colMap)) && Boolean(evalNode(node.b, row, colMap));\n    case \'not\': return !Boolean(evalNode(node.a, row, colMap));\n    case \'str\': return node.v;\n    case \'num\': return parseNum(node.v);\n    case \'col\': return getCell(row, node.name, colMap);\n    case \'call\': {\n      const fname = ci(node.name);\n      const args = node.args.map(a => evalNode(a, row, colMap));\n\n      if (fname === \'missing\') return isMissing(args[0]);\n      if (fname === \'num\') return parseNum(args[0]);\n\n      if (fname === \'contains\') {\n        const a = args[0], b = args[1];\n        if (isMissing(a) || isMissing(b)) return false;\n        return ci(a).includes(ci(b));\n      }\n      if (fname === \'startswith\') {\n        const a = args[0], b = args[1];\n        if (isMissing(a) || isMissing(b)) return false;\n        return ci(a).startsWith(ci(b));\n      }\n      if (fname === \'endswith\') {\n        const a = args[0], b = args[1];\n        if (isMissing(a) || isMissing(b)) return false;\n        return ci(a).endsWith(ci(b));\n      }\n\n      throw new Error(`Unknown function: ${node.name}`);\n    }\n    case \'cmp\': {\n      const op = ci(node.op);\n      const a = evalNode(node.a, row, colMap);\n      const b = evalNode(node.b, row, colMap);\n\n      if (op === \'<\' || op === \'<=\' || op === \'>\' || op === \'>=\') {\n        const na = parseNum(a);\n        const nb = parseNum(b);\n        if (na === null || nb === null) return false;\n        if (op === \'<\') return na < nb;\n        if (op === \'<=\') return na <= nb;\n        if (op === \'>\') return na > nb;\n        return na >= nb;\n      }\n\n      if (op === \'=\' || op === \'^=\' || op === \'ne\') {\n        const na = parseNum(a);\n        const nb = parseNum(b);\n        let eq;\n        if (na !== null && nb !== null) eq = (na === nb);\n        else {\n          const sa = ci(isMissing(a) ? \'\' : a);\n          const sb = ci(isMissing(b) ? \'\' : b);\n          eq = (sa === sb);\n        }\n        return (op === \'=\') ? eq : !eq;\n      }\n\n      throw new Error(`Unknown operator: ${node.op}`);\n    }\n    default:\n      return false;\n  }\n}\n\nfunction compileFormula(text) {\n  const t = text.trim();\n  if (!t) return { fn: (_row)=>true };\n  const tokens = tokenize(t);\n  const p = new Parser(tokens);\n  const ast = p.parse();\n  return { fn: (row) => Boolean(evalNode(ast, row, COL_MAP)) };\n}\n\nlet DATA = [];\nlet COLUMNS = [];\nlet COL_MAP = new Map();\nlet VIEW = [];\nlet VIEW_OBS = [];\nlet sortCol = null;\nlet sortDir = 1;\nlet ACTIVE_SHEET = \'\';\nlet SHEET_STATES = {};\nconst elTabBar = document.getElementById(\'tabbar\');\n\nconst elFormula = document.getElementById(\'formula\');\nconst elApply = document.getElementById(\'apply\');\nconst elClear = document.getElementById(\'clear\');\nconst elErr = document.getElementById(\'err\');\nconst elCount = document.getElementById(\'count\');\nconst elThead = document.getElementById(\'thead\');\nconst elTbody = document.getElementById(\'tbody\');\nconst elColJump = document.getElementById(\'coljump\');\nconst elJump = document.getElementById(\'jump\');\nconst elWrap = document.getElementById(\'wrap\');\nconst elColList = document.getElementById(\'colnames\');\nconst elBar = document.getElementById(\'bar\');\n\nfunction setError(msg) {\n  elErr.textContent = msg || \'\';\n  elErr.classList.toggle(\'show\', Boolean(msg));\n}\nfunction setCount() {\n  const filtered = VIEW.length !== DATA.length ? ` (filtered from ${DATA.length})` : \'\';\n  elCount.textContent = `${VIEW.length} obs${filtered} | ${COLUMNS.length} vars`;\n}\nfunction saveTabState(name) {\n  SHEET_STATES[name] = { data: DATA, columns: COLUMNS, colMap: COL_MAP, view: VIEW, viewObs: VIEW_OBS, sortCol, sortDir, filterText: elFormula.value, filterActive: elFormula.classList.contains(\'active\') };\n}\n\nfunction loadTabState(name) {\n  const s = SHEET_STATES[name];\n  if (!s) return;\n  DATA = s.data; COLUMNS = s.columns; COL_MAP = s.colMap; VIEW = s.view; VIEW_OBS = s.viewObs;\n  sortCol = s.sortCol; sortDir = s.sortDir;\n  elFormula.value = s.filterText;\n  elFormula.classList.toggle(\'active\', s.filterActive);\n  setError(\'\');\n}\n\nfunction switchTab(name) {\n  if (ACTIVE_SHEET === name) return;\n  saveTabState(ACTIVE_SHEET);\n  ACTIVE_SHEET = name;\n  loadTabState(name);\n  elTabBar.querySelectorAll(\'.tab\').forEach(t => t.classList.toggle(\'active\', t.dataset.sheet === name));\n  populateColDatalist();\n  refreshUI();\n}\n\nfunction adjustWrapHeight() {\n  elWrap.style.height = `calc(100vh - ${elBar.offsetHeight}px)`;\n}\n\nfunction appendSortArrow(el) {\n  const arrow = document.createElement(\'span\');\n  arrow.className = \'sort-arrow\';\n  arrow.textContent = sortDir === 1 ? \'\u25b2\' : \'\u25bc\';\n  el.appendChild(arrow);\n}\n\nfunction refreshUI() {\n  applySort(); setCount(); renderHeader(); renderBody(); adjustWrapHeight();\n}\n\nfunction buildColumns(data) {\n  const set = new Set();\n  for (const row of data) {\n    if (row && typeof row === \'object\' && !Array.isArray(row)) {\n      for (const k of Object.keys(row)) set.add(k);\n    }\n  }\n  return Array.from(set);\n}\n\nfunction renderHeader() {\n  const tr = document.createElement(\'tr\');\n  const thObs = document.createElement(\'th\');\n  const isObsSort = sortCol === \'__obs__\';\n  thObs.textContent = \'Obs\';\n  if (isObsSort) appendSortArrow(thObs);\n  thObs.className = \'obs\';\n  thObs.style.cursor = \'pointer\';\n  thObs.title = \'Sort by original observation order\';\n  thObs.addEventListener(\'click\', () => {\n    if (sortCol === \'__obs__\') sortDir *= -1;\n    else { sortCol = \'__obs__\'; sortDir = 1; }\n    applySort();\n    renderHeader();\n    renderBody();\n  });\n  tr.appendChild(thObs);\n  for (const col of COLUMNS) {\n    const th = document.createElement(\'th\');\n    const isSort = sortCol && ci(sortCol) === ci(col);\n    th.textContent = col;\n    if (isSort) appendSortArrow(th);\n    th.dataset.col = col;\n    th.title = col;\n    th.addEventListener(\'click\', () => {\n      if (sortCol && ci(sortCol) === ci(col)) sortDir *= -1;\n      else { sortCol = col; sortDir = 1; }\n      applySort();\n      renderHeader();\n      renderBody();\n    });\n    tr.appendChild(th);\n  }\n  elThead.textContent = \'\';\n  elThead.appendChild(tr);\n}\n\nfunction renderBody() {\n  const rowsToRender = VIEW.slice(0, 5000);\n  const obsToRender = VIEW_OBS.slice(0, 5000);\n  const frag = document.createDocumentFragment();\n  for (let i = 0; i < rowsToRender.length; i++) {\n    const row = rowsToRender[i];\n    const tr = document.createElement(\'tr\');\n    const tdObs = document.createElement(\'td\');\n    tdObs.className = \'obs\';\n    tdObs.textContent = obsToRender[i];\n    tr.appendChild(tdObs);\n    for (const col of COLUMNS) {\n      const td = document.createElement(\'td\');\n      const v = row ? row[col] : undefined;\n      if (v === null || v === undefined || (typeof v === \'string\' && v.trim() === \'\')) {\n        td.textContent = \'.\';\n        td.setAttribute(\'data-missing\', \'\');\n      } else {\n        td.textContent = String(v);\n      }\n      tr.appendChild(td);\n    }\n    frag.appendChild(tr);\n  }\n  elTbody.textContent = \'\';\n  elTbody.appendChild(frag);\n}\n\nfunction applySort() {\n  if (!sortCol) return;\n  const paired = VIEW.map((r, i) => [r, VIEW_OBS[i]]);\n  if (sortCol === \'__obs__\') {\n    paired.sort(([, a], [, b]) => (a - b) * sortDir);\n    VIEW = paired.map(p => p[0]);\n    VIEW_OBS = paired.map(p => p[1]);\n    return;\n  }\n  const real = COL_MAP.get(ci(sortCol));\n  if (!real) return;\n  paired.sort(([r1], [r2]) => {\n    const a = r1 ? r1[real] : undefined;\n    const b = r2 ? r2[real] : undefined;\n    const ma = isMissing(a);\n    const mb = isMissing(b);\n    if (ma && mb) return 0;\n    if (ma) return 1 * sortDir;\n    if (mb) return -1 * sortDir;\n    return cmpValues(a, b) * sortDir;\n  });\n  VIEW = paired.map(p => p[0]);\n  VIEW_OBS = paired.map(p => p[1]);\n}\n\nfunction applyFilter() {\n  setError(\'\');\n  let compiled;\n  try { compiled = compileFormula(elFormula.value); }\n  catch (e) { setError(String(e && e.message ? e.message : e)); return; }\n\n  const filtered = [];\n  const obs = [];\n  try {\n    DATA.forEach((r, i) => {\n      if (compiled.fn(r)) { filtered.push(r); obs.push(i + 1); }\n    });\n  } catch (e) { setError(String(e && e.message ? e.message : e)); return; }\n  VIEW = filtered;\n  VIEW_OBS = obs;\n  elFormula.classList.toggle(\'active\', elFormula.value.trim().length > 0);\n  refreshUI();\n}\n\nfunction clearFilter() {\n  elFormula.value = \'\';\n  elFormula.classList.remove(\'active\');\n  setError(\'\');\n  VIEW = DATA.slice();\n  VIEW_OBS = DATA.map((_, i) => i + 1);\n  refreshUI();\n}\n\nfunction populateColDatalist() {\n  elColList.textContent = \'\';\n  for (const c of COLUMNS) {\n    const o = document.createElement(\'option\');\n    o.value = c;\n    elColList.appendChild(o);\n  }\n}\n\nfunction jumpToColumn() {\n  const target = elColJump.value.trim();\n  if (!target) return;\n  const real = COL_MAP.get(ci(target));\n  if (!real) { setError(`Unknown column: ${target}`); return; }\n  setError(\'\');\n\n  const ths = elThead.querySelectorAll(\'th[data-col]\');\n  let idx = -1;\n  for (let i=0; i<ths.length; i++) {\n    if (ci(ths[i].dataset.col) === ci(real)) { idx = i; break; }\n  }\n  if (idx < 0) return;\n\n  ths.forEach(t => t.classList.remove(\'hl\'));\n  const th = ths[idx];\n  th.classList.add(\'hl\');\n\n  const left = th.offsetLeft;\n  const right = left + th.offsetWidth;\n  const viewLeft = elWrap.scrollLeft;\n  const viewRight = viewLeft + elWrap.clientWidth;\n  if (left < viewLeft) elWrap.scrollLeft = left;\n  else if (right > viewRight) elWrap.scrollLeft = right - elWrap.clientWidth;\n}\n\nfunction exportJSON() {\n  const name = ACTIVE_SHEET || \'export\';\n  const ts = Date.now();\n  const blob = new Blob([JSON.stringify(VIEW, null, 2)], {type: \'application/json\'});\n  const a = document.createElement(\'a\');\n  a.href = URL.createObjectURL(blob);\n  a.download = `${name}_export_${ts}.json`;\n  a.click();\n  URL.revokeObjectURL(a.href);\n}\n\nfunction exportCSV() {\n  const name = ACTIVE_SHEET || \'export\';\n  const ts = Date.now();\n  const esc = v => {\n    const s = (v === null || v === undefined) ? \'\' : String(v);\n    return (s.includes(\',\') || s.includes(\'"\') || s.includes(\'\\n\')) ? \'"\' + s.replace(/"/g, \'""\') + \'"\' : s;\n  };\n  const lines = [COLUMNS.map(esc).join(\',\')];\n  for (const row of VIEW) lines.push(COLUMNS.map(c => esc(row[c])).join(\',\'));\n  const blob = new Blob([lines.join(\'\\r\\n\')], {type: \'text/csv\'});\n  const a = document.createElement(\'a\');\n  a.href = URL.createObjectURL(blob);\n  a.download = `${name}_export_${ts}.csv`;\n  a.click();\n  URL.revokeObjectURL(a.href);\n}\n\nelApply.addEventListener(\'click\', applyFilter);\nelClear.addEventListener(\'click\', clearFilter);\nelJump.addEventListener(\'click\', jumpToColumn);\nelColJump.addEventListener(\'keydown\', (e) => { if (e.key === \'Enter\') jumpToColumn(); });\nelFormula.addEventListener(\'keydown\', (e) => { if (e.key === \'Enter\' && (e.ctrlKey || e.metaKey)) applyFilter(); });\ndocument.getElementById(\'expjson\').addEventListener(\'click\', exportJSON);\ndocument.getElementById(\'expcsv\').addEventListener(\'click\', exportCSV);\n\n(async function init() {\n  const res = await fetch(\'/data\');\n  const payload = await res.json();\n  const sheetNames = payload.sheets;\n  const allData = payload.data;\n\n  if (sheetNames && sheetNames.length > 1) {\n    elTabBar.style.display = \'\';\n    for (const name of sheetNames) {\n      const rows = allData[name] || [];\n      const cols = buildColumns(rows);\n      const cmap = buildColMap(cols);\n      SHEET_STATES[name] = {\n        data: rows, columns: cols, colMap: cmap,\n        view: rows.slice(), viewObs: rows.map((_, i) => i + 1),\n        sortCol: null, sortDir: 1, filterText: \'\', filterActive: false\n      };\n      const btn = document.createElement(\'div\');\n      btn.className = \'tab\';\n      btn.textContent = name;\n      btn.dataset.sheet = name;\n      btn.addEventListener(\'click\', () => switchTab(name));\n      elTabBar.appendChild(btn);\n    }\n    ACTIVE_SHEET = sheetNames[0];\n    loadTabState(ACTIVE_SHEET);\n    elTabBar.querySelector(\'.tab\').classList.add(\'active\');\n  } else {\n    const key = sheetNames ? sheetNames[0] : \'\';\n    const rows = allData[key !== undefined ? key : \'\'] || [];\n    DATA = rows;\n    ACTIVE_SHEET = key || \'\';\n    COLUMNS = buildColumns(DATA);\n    COL_MAP = buildColMap(COLUMNS);\n    VIEW = DATA.slice();\n    VIEW_OBS = DATA.map((_, i) => i + 1);\n  }\n\n  populateColDatalist();\n  setCount();\n  renderHeader();\n  renderBody();\n  adjustWrapHeight();\n  new ResizeObserver(adjustWrapHeight).observe(elBar);\n})();\n</script>\n</body>\n</html>\n'


def _pick_port(port: int) -> int:
    if port != 0:
        return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def view_json_array(
    input_path: str,
    port: int = 0,
    open_browser: bool = True,
    sheet: Optional[str] = None,
    raw_top: Optional[float] = None,
    header_row: Optional[int] = None,
) -> None:
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)

    ext = os.path.splitext(input_path)[1].lower()

    if ext in ('.xlsm', '.xlsx'):
        sheets_dict = parse_xlsx(input_path, sheet=sheet, raw_top=raw_top, header_row=header_row)
        sheet_names = [name for name in sheets_dict.keys() if name != '__raw__']
        payload = _dumps({
            "sheets": sheet_names,
            "data": sheets_dict,
        })
    elif ext == '.csv':
        if raw_top is not None:
            with open(input_path, newline='', encoding='utf-8-sig') as _f:
                reader = csv.reader(_f)
                all_rows = [(i + 1, list(row)) for i, row in enumerate(reader)]
            all_rows = [(rn, cells) for rn, cells in all_rows if any(c.strip() for c in cells)]
            n = max(int(len(all_rows) * raw_top / 100), 10)
            raw_rows = [{"_row": rn, "_col": list(range(len(cells))), "_cells": cells} for rn, cells in all_rows[:n]]
            payload = _dumps({"sheets": None, "data": {"": raw_rows, "__raw__": True}})
        else:
            with open(input_path, newline='', encoding='utf-8-sig') as _f:
                reader = csv.DictReader(_f)
                arr = [dict(row) for row in reader]
            payload = _dumps({"sheets": None, "data": {"": arr}})
    else:
        # JSON array (legacy .json / .jsonl / no extension)
        import json as _json
        with open(input_path, 'rb') as _f:
            raw = _f.read()
        arr = _json.loads(raw)
        if not isinstance(arr, list):
            raise ValueError("JSON file must be an array of objects")
        payload = _dumps({"sheets": None, "data": {"": arr}})

    chosen_port = _pick_port(port)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                body = _VIEW_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path in ("/data", "/data/"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)
                return

            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            return

    httpd = HTTPServer(("127.0.0.1", chosen_port), Handler)
    url = f"http://127.0.0.1:{chosen_port}/"

    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    if open_browser:
        webbrowser.open(url)

    try:
        print(f"Viewer running at {url}")
        print("Press Ctrl+C to stop")
        while True:
            t.join(1)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()


def _build_view_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="csvseljson view",
        add_help=True,
        description="View CSV, xlsx, xlsm, or JSON tabular data in a local browser.",
    )
    p.add_argument("json", help="Path to JSON array file")
    p.add_argument("--port", type=int, default=0, help="Port to use (0 = choose a free port)")
    p.add_argument("--no-open", action="store_true", help="Do not open the browser automatically")
    p.add_argument(
        "--sheet",
        default=None,
        help="Sheet name or 0-based index to open (xlsx only). Default: all sheets as tabs.",
    )
    hdr_group = p.add_mutually_exclusive_group()
    hdr_group.add_argument(
        "--raw-top",
        type=float,
        default=None,
        metavar="PCT",
        help="Return raw rows (no header detection) for first PCT%% of sheet, min 10 rows.",
    )
    hdr_group.add_argument(
        "--header-row",
        type=int,
        default=None,
        metavar="N",
        help="Use row N as header (1-based). Overrides auto-detection.",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0].lower() != 'view':
        parser = argparse.ArgumentParser(
            prog="csvseljson",
            add_help=True,
            description="Serve tabular data in a local browser. Only the 'view' subcommand is supported.",
        )
        parser.add_argument("subcommand", choices=["view"], help="Subcommand to run")
        parser.parse_args(argv)
        return 0

    vp = _build_view_parser()
    args = vp.parse_args(argv[1:])
    view_json_array(
        args.json,
        port=args.port,
        open_browser=(not args.no_open),
        sheet=getattr(args, 'sheet', None),
        raw_top=getattr(args, 'raw_top', None),
        header_row=getattr(args, 'header_row', None),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
