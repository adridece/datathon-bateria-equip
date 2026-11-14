"""
Prepara el projecte despres de clonar-lo (funciona igual a Windows i Mac):
    python scripts/setup.py
Descomprimeix les dades del paquet oficial a data/raw/ i genera data/processed/hourly.csv
"""
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "data" / "package" / "paquet_participants_datathon_upc.zip"
RAW = ROOT / "data" / "raw" / "train"

if not RAW.exists():
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(ZIP).extractall(tmp)
        src = next(Path(tmp).rglob("data/train"))
        RAW.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, RAW)
    print("Dades descomprimides a", RAW)

sys.path.insert(0, str(ROOT))
from src.data import load_hourly  # noqa: E402

df = load_hourly(force=True)
print("Taula horaria:", df.shape, "->", ROOT / "data" / "processed" / "hourly.csv")
