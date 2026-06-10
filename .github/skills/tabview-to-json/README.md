# tabview-to-json

`tabview-to-json` is a Windows-friendly extraction skill and script bundle for turning tabular files into JSON without writing custom parsers.

The intended agent path is headless:

- `scripts/extract.py` is the primary entrypoint for CSV, `.xlsx`, and `.xlsm` extraction.
- `python -m scripts view ...` is manual viewer infrastructure, not the default automation path.
- Unknown-structure `.xlsm` work follows a fixed discovery chain: `--sheet _dummy_` -> `--raw-top` -> `--header-row`.

This repository also includes a repeatable compliance-eval harness for measuring whether agent handoffs actually follow the skill, especially on unknown-structure `.xlsm` discovery.

## What This Project Contains

Core extraction surface:

- `scripts/extract.py` - headless extractor used by agents
- `scripts/csvseljson.py` - local viewer and `/data` backend used by `extract.py`
- `scripts/__main__.py` - module dispatch so `python -m scripts ...` works
- `SKILL.md` - skill instructions
- `agent.md` - agent-facing operating manual
- `reference/` - filter syntax, API contract, and troubleshooting docs

Validation and eval surface:

- `tests/` - unit and regression coverage for extraction and controller behavior
- `evals/compliance_controller.py` - repeatable campaign controller for compliance evals
- `evals/evals.json` - canonical prompt/eval set for the skill
- `evals/files/` - local evaluation inputs
- `.github/agents/gpt-4o.agent.md` - evaluation handoff definition for GPT-4o
- `.github/agents/gpt-5-mini.agent.md` - evaluation handoff definition for GPT-5 mini

Generated campaign artifacts live outside the repo in the sibling workspace folder:

- `c:\Users\LinM1\.claude\skills\tabview-to-json-workspace`

## Environment

This repo is designed around the Windows setup used in this workspace.

- Use `python` directly on Windows.
- `.xlsm` parsed directly as zip/XML — no Excel or PowerShell required.
- The extraction scripts target Python 3.8+.
- The compliance controller currently uses newer type syntax and should be treated as Python 3.10+.

There is no project-local dependency bootstrap script. In this workspace, the scripts run with the existing Python installation.

## Supported Inputs

- `.csv`
- `.xlsx`
- `.xlsm` (macros ignored; no Excel required)

Not supported:

- `.xls` directly; save it as `.xlsx` first

## Quick Start

Run from the repository root.

### Headless extraction

```powershell
python scripts\extract.py data.csv --out result.json

python scripts\extract.py study.xlsx --sheet ADSL --where "int(AGE or 0) > 50 and SEX == 'F'" --cols USUBJID AGE SEX ARM --out adsl_filtered.json

python -m scripts evals/files/file.xlsm --sheet Status --header-row 6 --where "'Mark Lin' in str(row.get('QC Programmer(s)', ''))" --cols 1 2 --out result.json
```

### Manual viewer

Only use the viewer when a human explicitly wants to inspect the table visually.

```powershell
python -m scripts view result.json
python scripts\extract.py data.xlsx --out result.json --view
```

## Unknown-Structure `.xlsm` Workflow

For ambiguous `.xlsm` work, the project deliberately uses a strict discovery sequence.

1. Discover sheets with a guaranteed-miss sheet name.
2. Probe raw rows on the chosen sheet.
3. Extract with the discovered header row.

Example:

```powershell
python -m scripts evals/files/file.xlsm --sheet _dummy_
python -m scripts evals/files/file.xlsm --sheet Status --raw-top 5
python -m scripts evals/files/file.xlsm --sheet Status --header-row 6 --where "'Mark Lin' in str(row.get('QC Programmer(s)', ''))" --cols 1 2 --out result.json
```

Rules that matter:

- Do not invent flags like `--probe` or `--sheet-info`.
- Do not combine `--raw-top` and `--header-row` in the same command.
- Do not switch to pandas, openpyxl, xlrd, or custom CSV/XLSX parsing.
- If the user asked for only `Output Identifier` and `Title`, keep the result to `--cols 1 2`.

## Tests

Run the full suite with:

```powershell
python -m pytest tests -q
```

The current focused regression coverage includes:

- header auto-detection
- duplicate headers
- row numbering for `.xlsx`
- view-only CLI behavior
- compliance controller normalization and audit rules
- guidance locks for the unknown-structure `.xlsm` workflow

## Compliance Evals

The repeatable compliance path is `evals/compliance_controller.py`.

Its job is to:

- create a normalized campaign directory for a prompt set
- emit per-run worker instructions and skeleton artifacts
- define what counts as compliance
- normalize incomplete or malformed worker metadata
- summarize the campaign into `campaign_summary.json` and `campaign_summary.md`

The controller is built for the unknown-structure `file.xlsm` Mark Lin extraction scenario, where the correct compliant outcome is:

- sheet = `Status`
- header row = `6`
- output rows = `17`
- output columns = exactly `Output Identifier`, `Title`
- no browser flow
- no custom parser code
- required worker artifacts present

### Campaign Layout

Preparing a campaign creates a sibling workspace tree like this:

```text
tabview-to-json-workspace/
  gpt5mini-compliance/
    iteration-2/
      eval_manifest.json
      campaign_summary.json
      campaign_summary.md
      run-01-base-unknown-structure/
        prompt.txt
        worker_prompt.txt
        commands.txt
        process_log.md
        transcript.txt
        metadata.json
        outputs/
          result.json
```

### Prepare a Campaign

Example GPT-5 mini campaign:

```powershell
python evals/compliance_controller.py prepare --campaign-slug gpt5mini-compliance --agent-label gpt-5-mini --model-label "GPT-5 mini (copilot)" --workspace-root "c:\Users\LinM1\.claude\skills\tabview-to-json-workspace"
```

Example GPT-4o campaign:

```powershell
python evals/compliance_controller.py prepare --campaign-slug gpt4o-compliance --agent-label gpt-4o --model-label "GPT-4o (copilot)" --workspace-root "c:\Users\LinM1\.claude\skills\tabview-to-json-workspace"
```

This prints the created iteration directory. Each run folder then contains a `worker_prompt.txt` file ready to hand to a subagent.

### Handoff Manual: GPT-4o and GPT-5 mini

Two handoff definitions are checked into `.github/agents/`:

- `.github/agents/gpt-4o.agent.md`
- `.github/agents/gpt-5-mini.agent.md`

Both are minimal evaluation agents. They are expected to:

- read `SKILL.md` when a worker prompt points at the skill path
- follow the skill instructions exactly
- save artifacts into the run directory specified by the worker prompt
- write a compact `transcript.txt`

There are two practical ways to hand off a run:

### Option 1: model-pinned handoff

Use the run directory's `worker_prompt.txt` as the full task body and pin the model explicitly.

GPT-4o:

```text
model: GPT-4o (copilot)
prompt: <contents of run-XX-.../worker_prompt.txt>
```

GPT-5 mini:

```text
model: GPT-5 mini (copilot)
prompt: <contents of run-XX-.../worker_prompt.txt>
```

### Option 2: agent-file handoff

Use the checked-in agent definitions as the reusable handoff templates and feed them the `worker_prompt.txt` task.

This is the preferred path if you want the campaign to stay consistent with the repo-local evaluation agents.

### Running a 10-slot Campaign Manually

1. Run `prepare` for the desired campaign slug.
2. Open the printed iteration directory.
3. For each `run-XX-*` folder, pass `worker_prompt.txt` to either GPT-4o or GPT-5 mini.
4. Wait for all workers to finish writing artifacts.
5. Run `summarize` on the iteration directory.

Example summarize command:

```powershell
python evals/compliance_controller.py summarize "c:\Users\LinM1\.claude\skills\tabview-to-json-workspace\gpt5mini-compliance\iteration-2"
```

### What the Controller Scores as Compliant

A run is fully compliant only if all of the following hold:

- extraction path was used
- sheet discovery happened with `--sheet _dummy_`
- raw probing happened with `--raw-top`
- final extraction happened with `--header-row`
- no `--view`
- no custom parser code
- selected sheet is `Status`
- header row is `6`
- result has `17` rows
- result has exactly `2` columns
- keys are `Output Identifier` and `Title`
- required audit artifacts exist
- no disallowed invented flags appear in the logged commands

### Historical Campaign Notes

The current workspace already contains example campaign outputs:

- `c:\Users\LinM1\.claude\skills\tabview-to-json-workspace\gpt4o-compliance\iteration-1`
- `c:\Users\LinM1\.claude\skills\tabview-to-json-workspace\gpt5mini-compliance\iteration-2`

From the latest GPT-5 mini summary in this workspace:

- 10 slots launched
- 2 fully compliant runs
- 7 runs with non-empty `result.json`
- 0 runs with invented probe flags
- 1 controller-normalized run

These artifacts are useful as reference examples when changing the controller or tightening the skill.

## Notes on Older Eval Scripts

The `evals/` folder still contains older one-off scripts such as `write_metadata.py`, `check_outputs.py`, `grade_iteration*.py`, and `restructure_dirs.py`.

Those scripts were used in earlier iteration-specific workflows. The repeatable path going forward is:

- `evals/compliance_controller.py prepare`
- worker handoffs via `worker_prompt.txt`
- `evals/compliance_controller.py summarize`

## Recommended Reading Order

If you are new to the repo, read in this order:

1. `README.md`
2. `SKILL.md`
3. `agent.md`
4. `reference/error-playbook.md`
5. `evals/compliance_controller.py`
6. `tests/test_compliance_controller.py`

## Current Verification

Latest local verification in this workspace:

```powershell
python -m pytest tests -q
```

Result at the time this README was added:

- `55 passed`