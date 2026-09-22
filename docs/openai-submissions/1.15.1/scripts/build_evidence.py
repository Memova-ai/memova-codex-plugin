"""Rebuild source-only inventories and a deterministic candidate ZIP. No remote writes."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
REV = "9e699f05c2beb3bcba3ed636e3fcf7713421c3a8"
BASE = "v1.15.0"

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

files = git("ls-tree", "-r", "--name-only", REV, "plugins/memova").decode().splitlines()
payload = {name: git("show", f"{REV}:{name}") for name in files}
manifest = [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(payload.items())]
write("source-files.json", {"revision": REV, "files": manifest})
skills = []
for name, data in sorted(payload.items()):
    if not name.endswith("/SKILL.md"):
        continue
    old = git("ls-tree", "--name-only", BASE, name).decode().strip()
    state = "new" if not old else "unchanged" if git("show", f"{BASE}:{name}") == data else "changed"
    folder = name.rsplit("/", 1)[0]
    skills.append({"name": folder.rsplit("/", 1)[1], "path": name, "delta_from_1_15_0": state,
                   "sha256": hashlib.sha256(data).hexdigest(),
                   "bundled_files": [f for f in files if f.startswith(folder + "/")],
                   "shared_dependencies": "plugins/memova/scripts; cross-skill paths retained in full source ZIP",
                   "portal_scan": "NOT_RUN", "host_acceptance": "NOT_RUN"})
write("skill-inventory.json", skills)
zipname = OUT / "memova-1.15.1-source-candidate.zip"
with zipfile.ZipFile(zipname, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, data in sorted(payload.items()):
        info = zipfile.ZipInfo(name, (2026, 9, 22, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, data)
with zipfile.ZipFile(zipname) as z:
    assert sorted(z.namelist()) == sorted(payload)
    for name, data in payload.items():
        assert z.read(name) == data
write("package-receipt.json", {"revision": REV, "file": zipname.name, "files": len(payload),
      "skills": len(skills), "bytes": zipname.stat().st_size,
      "sha256": hashlib.sha256(zipname.read_bytes()).hexdigest(),
      "source_byte_parity": True,
      "status": "SOURCE_EVIDENCE_ONLY_NOT_PORTAL_APPROVED",
      "note": "Complete repository-relative plugin tree; Portal upload shape and host script paths require verification."})
print(json.dumps({"files": len(files), "skills": len(skills), "zip": zipname.name}))
