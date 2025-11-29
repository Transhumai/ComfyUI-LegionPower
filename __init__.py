# Aggiunge la cartella 'src' al percorso di ricerca di Python per questo package
#import sys
#from pathlib import Path

#sys.path.insert(0, str(Path(__file__).parent / "src"))

# Ora importa e riesporta tutto dal nostro "vero" __init__.py
from .src.comfyui_legion_power import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']