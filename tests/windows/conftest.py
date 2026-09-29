import sys
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[2] / "experiments" / "epistemic-diversity"
sys.path.insert(0, str(EXPERIMENT))
sys.path.insert(0, str(EXPERIMENT / "src"))
