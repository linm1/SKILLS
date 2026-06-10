"""Test that --limit flag is accepted by extract.py."""
import subprocess
import sys
import os

EXTRACT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'extract.py')


def test_limit_arg_in_help():
    """--limit should appear in extract.py --help output."""
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        [sys.executable, EXTRACT, "--help"],
        capture_output=True, text=True, encoding='utf-8', env=env
    )
    assert "--limit" in result.stdout, f"--limit not in help:\n{result.stdout}"
