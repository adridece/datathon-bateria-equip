"""
Crea submissions/<nom>.zip a partir d'una carpeta d'agent i el valida amb el checker oficial.
    python scripts/make_submission.py agents/estandard_lp
Posa agent.py i els fitxers auxiliars (json, pkl, py) a l'ARREL del zip, com demana la web.
"""
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
folder = Path(sys.argv[1]).resolve()
files = [f for f in folder.iterdir() if f.is_file() and f.suffix in {".py", ".json", ".pkl", ".txt"}]
assert any(f.name == "agent.py" for f in files), "Falta agent.py"
out = ROOT / "submissions" / f"{folder.name}_{datetime.now():%m%d_%H%M}.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f, f.name)
print("Creat:", out, [f.name for f in files])
subprocess.run([sys.executable, str(ROOT / "starter_kit" / "check_submission.py"), str(out)], check=False)
