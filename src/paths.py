"""Repository paths shared by CLI, tests, and integration callers."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CORPUS = DATA / "mevzuat_derlemi"
