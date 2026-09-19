import json
import subprocess

FILES = [
    "get_stats.py",
    "ixl_parser.py",
    "ixl_scraper.py",
    "ixl_session.py",
    "math_academy_scraper.py",
    "progress.py",
    "report.py",
    "runtime.py",
    "scraper_base.py",
]


def _radon(command):
    result = subprocess.run(
        ["uvx", "--from", "radon==6.0.1", "radon", command, "-j", *FILES],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_metrics_probe():
    raise AssertionError(json.dumps({"cc": _radon("cc"), "mi": _radon("mi")}, indent=2))
