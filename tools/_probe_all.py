import json
import subprocess
from pathlib import Path

ROOT = Path(r"D:\music")
recs = json.load(open(ROOT / "_research" / "resolve.json", encoding="utf-8"))
state = json.load(open(ROOT / "_research" / "download_state.json", encoding="utf-8"))

rows = []
seen = set()
for k, st in sorted(state.items(), key=lambda kv: int(kv[0])):
    f = st.get("file")
    if not f or f in seen:
        continue
    seen.add(f)
    p = Path(f)
    if not p.exists():
        print("MISSING", f)
        continue
    out = subprocess.run(
        [str(ROOT / "bbdown" / "ffprobe.exe"), "-v", "error",
         "-show_entries", "format=duration,bit_rate", "-show_entries",
         "stream=codec_name,sample_rate", "-of", "default=nw=1", str(p)],
        capture_output=True, text=True).stdout
    info = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    rows.append((int(k), p, info))

for k, p, i in rows:
    br = int(i.get("bit_rate") or 0) // 1000
    if br < 200:
        print("LOW %4d %5dk %s %s" % (k + 1, br, p.suffix, p.name))

bad = []
for k, p, i in rows:
    dur = float(i.get("duration") or 0)
    exp = recs[k]["duration"]
    if dur and abs(dur - exp) > 20 and exp > 0:
        bad.append((k + 1, exp, round(dur), p.name))

print("duration mismatches", len(bad))
for b in bad[:15]:
    print("  ", b)
