---
name: sas-schema
description: 'Portable bundled SAS schema workflow. Use when you need to analyze or list SAS7BDAT files without a preinstalled sas-schema command, run the bundled Python entrypoint, or adjust the vendored analyze/list behavior inside this skill.'
argument-hint: 'What SAS file, folder, or portable sas-schema task do you need help with?'
---

# SAS Schema

This skill is self-contained. Do not assume a global `sas-schema` command or a checked-out repository. Use the bundled resources in this skill folder.

## Portability

The bundle targets **Python 3.8+ on Linux, macOS, or Windows**. The source uses only `typing`-based annotations and stdlib that exists on 3.8, so the floor is the dependency set, not the code. `requirements.txt` pins `pandas` and `numpy` with environment markers so a single `pip install -r ./scripts/requirements.txt` resolves to 3.8-compatible versions on Python 3.8 and to current versions on 3.9+. If you change dependencies, keep that floor intact — `pandas>=2.1` and `numpy>=1.25` dropped Python 3.8 and will break the promise.

## Bundled Resources

- Entry point: [run_sas_schema.py](./scripts/run_sas_schema.py)
- Dependency list: [requirements.txt](./scripts/requirements.txt)
- CLI implementation: [cli.py](./scripts/portable_sas_schema/cli.py)
- Core analysis logic: [schema_analyzer.py](./scripts/portable_sas_schema/core/schema_analyzer.py)
- Date and type helpers: [date_analyzer.py](./scripts/portable_sas_schema/core/date_analyzer.py), [type_analyzer.py](./scripts/portable_sas_schema/core/type_analyzer.py)

## When to Use

- Run or explain schema extraction without relying on a preinstalled `sas-schema` command
- Choose between discovery, single-file analysis, and batch analysis
- Hand off a portable analyze/list workflow to another user
- Tune `--threshold`, `--recursive`, `--max-files`, `--indent`, `--output`, or `--debug`
- Modify the bundled Python implementation instead of a separate source repository

## Procedure

1. Start from this skill folder, not from an external repository.
2. Verify Python and install the bundled dependencies if needed.
   - Check Python: `python --version`
   - Install requirements: `python -m pip install -r ./scripts/requirements.txt`
   - On the team Linux server use `/bin/python3.8`, or the repo's `.venv` created by `setup.sh` at repo root (`./.venv/bin/python`).
3. Smoke test the bundled CLI.
   - Run: `python ./scripts/run_sas_schema.py --help`
4. Identify the requested outcome.
   - Find candidate `.sas7bdat` files: `python ./scripts/run_sas_schema.py list <dir> [--recursive]`
   - Analyze one file: `python ./scripts/run_sas_schema.py analyze <file> [--threshold F] [--output FILE] [--debug]`
   - Analyze a folder: `python ./scripts/run_sas_schema.py analyze <dir> [--recursive] [--max-files N] [--threshold F] [--debug]`
   - Change behavior: edit [cli.py](./scripts/portable_sas_schema/cli.py) or the relevant file under `./scripts/portable_sas_schema/core/`
5. For `analyze`, branch by path type.
   - File path: expect schema JSON on stdout unless `--output` is set; exit code is non-zero when the JSON result reports `"success": false`
   - Directory path or `--batch`: expect one `.json` file next to each analyzed `.sas7bdat`, plus a JSON summary on stdout and a human-readable completion line on stderr; exit code is non-zero when any file failed (`failed_analyses > 0`)
   - stdout carries only JSON; the human-readable line goes to stderr. To consume the JSON, capture stdout alone — `... > out.json 2>/dev/null`, or `subprocess.run(..., stdout=PIPE, stderr=DEVNULL)`. Merging the two streams (e.g. PowerShell `$(...)`, `subprocess.check_output` without redirecting stderr) prepends the stderr line and makes the result unparseable.
6. Validate the narrowest slice after each change.
   - Parser and help changes: `python ./scripts/run_sas_schema.py --help`
   - CLI behavior changes: run one focused `list` or `analyze` command against a small test file or folder
   - Output contract changes: confirm the JSON parses and batch mode still writes sibling `.json` files

## Decision Points

- If `sas-schema` already exists on `PATH`, ignore it unless the user explicitly asks for the installed command. Prefer the bundled runner so the skill stays portable.
- If dependencies are missing, install from [requirements.txt](./scripts/requirements.txt) instead of pointing to another repository or shell wrapper.
- Prefer `list` before `analyze` when the user does not yet know which SAS files exist.
- Prefer single-file `analyze` with `--output` when the user wants one stable JSON artifact.
- Prefer batch `analyze` only for directories, and cap scope with `--max-files` when the directory contents are uncertain.
- Increase `--threshold` when too many columns are treated as categorical; decrease it when expected code lists are missing.
- Use `--debug` only when diagnosing parser or metadata issues. Normal JSON consumers should ignore stderr.
- If the user asks for MCP server features or SDTM Excel parsing, treat that as a separate expansion unless they explicitly want those modules bundled into this skill too.

## Quality Checks

- The skill does not depend on private paths, a checked-out repo, or a preinstalled `sas-schema` command.
- The bundled runner works via `python ./scripts/run_sas_schema.py --help`.
- The command matches the actual path type and requested outcome.
- JSON from `--output`, or from stdout **with stderr separated**, parses cleanly and includes `"success"`. (In batch mode stderr carries a completion line; do not capture it into the JSON — see step 5.)
- Batch runs create the expected sibling `.json` files.
- `file_path` / `folder_path` values in the JSON use OS-native separators (backslashes on Windows, forward slashes on Linux). Consumers should not assume a fixed separator.

## Notes

- The bundled entrypoint exposes the same `analyze` and `list` CLI surface as `sas-schema`.
- The portable bundle intentionally includes the analyze/list CLI only. It does not bundle the FastMCP server or the SDTM Excel tooling.
- The implementation supports `--batch`, `--recursive`, `--max-files`, `--threshold`, `--output`, `--debug`, and `--indent`.
- Keep future edits inside `./scripts/` so the skill stays self-contained.