"""Locate both checkout data and resources installed from a wheel."""

from importlib.resources import files
from pathlib import Path

_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_CHECKOUT = (_SOURCE_ROOT / "pyproject.toml").is_file() and (_SOURCE_ROOT / "data").is_dir()
ROOT = _SOURCE_ROOT if _CHECKOUT else Path.cwd()
DATA = _SOURCE_ROOT / "data" if _CHECKOUT else Path(str(files("iadepusula_data")))
CORPUS = DATA / "mevzuat_derlemi"
