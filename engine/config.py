"""Runtime paths for the pipeline.

Modules read `config.INPUT` / `config.OUTPUT` at call time, never at import time, so `--input` and `--output`
can point the engine at a different corpus without editing code.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "google_photos_raw_dataset.csv"
OUTPUT = ROOT / "output"


def configure(input_path=None, output_dir=None):
    """Point the engine at a different corpus or output directory. Returns the resolved pair."""
    global INPUT, OUTPUT
    if input_path:
        INPUT = Path(input_path).resolve()
        if not INPUT.exists():
            raise FileNotFoundError(f"corpus not found: {INPUT}")
    if output_dir:
        OUTPUT = Path(output_dir).resolve()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    return INPUT, OUTPUT


def add_arguments(parser):
    """Shared --input / --output flags."""
    parser.add_argument("--input", default=None, help="corpus CSV (default: the bundled 840-record synthetic file)")
    parser.add_argument("--output", default=None, help="output directory (default: ./output)")
    return parser
