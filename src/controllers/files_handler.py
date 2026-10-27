import sys
from pathlib import Path


def get_bundle_files(name: str):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return str(root.joinpath(*name.split('/')))
