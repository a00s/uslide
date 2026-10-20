"""Compatibility entry point: current caps use PLA and the native project layout."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('atualiza_tampas_nativo.py')),run_name='__main__')
