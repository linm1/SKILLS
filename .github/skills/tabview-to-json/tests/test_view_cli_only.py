import sys
from pathlib import Path
from typing import Optional
import subprocess

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import csvseljson


def test_main_rejects_legacy_convert_flags(capsys):
    with pytest.raises(SystemExit) as excinfo:
        csvseljson.main(["-i", "input.csv"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "unrecognized arguments" in captured.err.lower() or "invalid choice" in captured.err.lower()


def test_main_dispatches_view_subcommand(monkeypatch):
    calls = {}

    def fake_view_json_array(
        input_path: str,
        port: int = 0,
        open_browser: bool = True,
        sheet: Optional[str] = None,
        raw_top: Optional[float] = None,
        header_row: Optional[int] = None,
    ) -> None:
        calls.update(
            {
                "input_path": input_path,
                "port": port,
                "open_browser": open_browser,
                "sheet": sheet,
                "raw_top": raw_top,
                "header_row": header_row,
            }
        )

    monkeypatch.setattr(csvseljson, "view_json_array", fake_view_json_array)

    result = csvseljson.main(
        [
            "view",
            "data.json",
            "--port",
            "8765",
            "--no-open",
            "--sheet",
            "Status",
            "--header-row",
            "6",
        ]
    )

    assert result == 0
    assert calls == {
        "input_path": "data.json",
        "port": 8765,
        "open_browser": False,
        "sheet": "Status",
        "raw_top": None,
        "header_row": 6,
    }


def test_module_entrypoint_dispatches_view_help():
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "scripts", "view", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0
    assert "--no-open" in result.stdout
    assert "--header-row" in result.stdout