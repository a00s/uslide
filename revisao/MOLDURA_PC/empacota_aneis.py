"""Compatibility entry point: current design is direct U clips, no cradle."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parent.parent/"CLIPES_U/empacota_clipes_u.py"))
