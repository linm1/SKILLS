# /data Endpoint Contract

The csvseljson viewer exposes a single HTTP endpoint that returns all parsed data in JSON.

---

## Endpoint

```
GET http://127.0.0.1:<PORT>/data
```

No authentication. No query parameters. Returns the full dataset parsed at server startup.

---

## Response Shape

### xlsx (multi-sheet)

```json
{
  "sheets": ["Sheet1", "Sheet2", "Sheet3"],
  "data": {
    "Sheet1": [
      {"COL_A": "value", "COL_B": "value", ...},
      ...
    ],
    "Sheet2": [...],
    "Sheet3": [...]
  }
}
```

### xlsx (single sheet, via --sheet flag)

```json
{
  "sheets": ["ADSL"],
  "data": {
    "ADSL": [
      {"USUBJID": "001-001", "AGE": "34", ...},
      ...
    ]
  }
}
```

### CSV input

```json
{
  "sheets": null,
  "data": {
    "": [
      {"COL_A": "value", "COL_B": "value", ...},
      ...
    ]
  }
}
```

`sheets` is `null` for CSV. The data key is an empty string `""`.

---

## Field Types

All row values are strings. No type inference is applied by the server.

| Source type | JSON representation |
|---|---|
| String cell | `"value"` |
| Numeric cell | `"42"` or `"3.14"` |
| Boolean cell (`t="b"`) | `"1"` or `"0"` |
| Shared string (xlsx) | Resolved to string |
| Empty / missing cell | `""` |
| Missing numeric (SAS) | `""` |

---

## Fetching in Different Environments

### Bash / curl

```bash
# All data
curl -s http://127.0.0.1:8765/data

# Extract first sheet rows
curl -s http://127.0.0.1:8765/data | python3 -c "
import json, sys
d = json.load(sys.stdin)
sheet = (d['sheets'] or [''])[0]
print(json.dumps(d['data'][sheet], indent=2))
"
```

### Python (stdlib only)

```python
import json, urllib.request

with urllib.request.urlopen("http://127.0.0.1:8765/data") as r:
    payload = json.loads(r.read())

sheets = payload["sheets"]       # list of names, or None for CSV
data = payload["data"]           # dict: sheet_name → list of row dicts

# Get first sheet
sheet_name = (sheets or [""])[0]
rows = data[sheet_name]
```

### Node.js

```javascript
const http = require("http");
http.get("http://127.0.0.1:8765/data", (res) => {
  let body = "";
  res.on("data", (chunk) => body += chunk);
  res.on("end", () => {
    const payload = JSON.parse(body);
    const sheet = (payload.sheets || [""])[0];
    const rows = payload.data[sheet];
    console.log(rows.length, "rows");
  });
});
```

### PowerShell (Windows)

```powershell
$resp = Invoke-RestMethod http://127.0.0.1:8765/data
$sheet = if ($resp.sheets) { $resp.sheets[0] } else { "" }
$rows = $resp.data.$sheet
Write-Host "$($rows.Count) rows"
```

---

## Timing / Readiness

The server is ready when `/data` returns HTTP 200. Poll with backoff:

```python
import time, urllib.request, urllib.error

def wait_ready(port, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/data", timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False
```

`extract.py` handles this automatically.

---

## Other Endpoints

| Path | Description |
|---|---|
| `GET /` | Browser viewer HTML (not useful for agents) |
| `GET /data` | Full JSON payload (use this) |

All other paths return 404.
