# Entry point for the current assembly visualization.
# Use the CAD environment with trimesh installed.
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parent.parent / 'SELAGEM/gera_visual_montagem.py'), run_name='__main__')
