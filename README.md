# SKILLS

Ready-to-use AI helper skills for VS Code Copilot Chat.

## What's inside

- **tabview-to-json** — Turn a CSV or Excel (.xlsx/.xlsm) file into clean JSON data. Filter rows, pick columns, or view the table in your browser. No setup needed.
- **sas-schema** — Inspect SAS (`.sas7bdat`) data files and get their structure and schema as JSON. Needs a one-time setup.
- **qc-clinical-programming** — Independent QC for clinical-trial programming deliverables (SDTM, ADaM, TLFs, define.xml). No setup needed.
- **finding-your-unknowns** — Surface gaps between a spec and the real codebase before implementing: bug fixes, feature scoping, UI/UX, backend tuning, mid-task checks, and pre/post-merge reviews. No setup needed.

## First-time setup

Only needed for **sas-schema**. tabview-to-json works immediately with no setup.

1. Clone the repo:
   ```bash
   git clone https://github.com/linm1/SKILLS.git
   ```
2. Enter the folder:
   ```bash
   cd SKILLS
   ```
3. Run setup:
   ```bash
   bash setup.sh
   ```
   This creates a `.venv` folder and installs sas-schema's packages. By default it uses `/bin/python3.8`. To use a different Python:
   ```bash
   PYTHON=/path/to/python3 bash setup.sh
   ```

## Install via npx skills

List all skills in this repo:

```bash
npx skills@latest add linm1/SKILLS --list
```

Install one skill globally (example: finding-your-unknowns):

```bash
npx skills@latest add linm1/SKILLS --skill finding-your-unknowns --global
```

## How to use (VS Code Copilot Chat)

1. Open the SKILLS folder in VS Code.
2. Open Copilot Chat and switch to **Agent mode**.
3. Type `/tabview-to-json` or `/sas-schema`, or just describe what you want — for example, "convert sales.csv to JSON" — and Copilot will match the right skill automatically.
4. Type `/skills` in chat to see all available skills.

## Updating

Pull the latest version at any time:

```bash
git pull
```
