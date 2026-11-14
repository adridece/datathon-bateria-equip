"""
Genera la versio PUBLICA del projecte a ../datathon-public (o la carpeta que li passis),
nomes amb els fitxers de la llista i comprovant que no hi hagi res que no toqui.
    python scripts/export_public.py [carpeta_desti]
Despres, a la carpeta desti: git init, commit amb el vostre nom i push al repo public.
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "datathon-public"

# El que SI va al public (afegiu-hi coses si cal)
INCLUDE = ["README.md", "requirements.txt", ".gitignore", ".gitattributes",
           "agents", "src", "notebooks", "scripts/setup.py", "scripts/make_submission.py",
           "docs/DECISIONS.md", "docs/CONTEXT.md"]
SKIP_NAMES = {"__pycache__", ".ipynb_checkpoints", ".DS_Store"}
# Paraules que NO poden apareixer enlloc
BANNED = re.compile(r"claude|anthropic|gemini|openai|chatgpt|gpt-|copilot|opencode|helmcode|"
                    r"co-authored-by|generated with|AGENTS\.md|sk-[a-z]{2,4}_", re.I)

if DEST.exists():
    for p in DEST.iterdir():
        if p.name != ".git":
            shutil.rmtree(p) if p.is_dir() else p.unlink()
DEST.mkdir(parents=True, exist_ok=True)

for item in INCLUDE:
    src = ROOT / item
    if not src.exists():
        continue
    dst = DEST / item
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*SKIP_NAMES))
    else:
        shutil.copy2(src, dst)

problemes = []
for f in DEST.rglob("*"):
    if f.is_file() and ".git" not in f.parts:
        try:
            txt = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in BANNED.finditer(txt):
            problemes.append(f"{f.relative_to(DEST)}: '{m.group(0)}'")
if problemes:
    print("ATENCIO, cal netejar abans de publicar:")
    print("\n".join(problemes))
    sys.exit(1)
print("Exportat net a", DEST)
