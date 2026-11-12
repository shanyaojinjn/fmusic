import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\music")
DEST = ROOT / "downloads"
recs = json.load(open(ROOT / "_research" / "resolve.json", encoding="utf-8"))
state = json.load(open(ROOT / "_research" / "download_state.json", encoding="utf-8"))

groups = defaultdict(list)
seen = set()
for k, st in sorted(state.items(), key=lambda kv: int(kv[0])):
    f = st.get("file")
    if not f or f in seen:
        continue
    p = Path(f)
    if not p.exists():
        continue
    seen.add(f)
    rec = recs[int(k)]
    m = rec.get("match") or {}
    title = "%s - %s" % (m.get("artist") or rec["artist"] or "未知歌手",
                         m.get("name") or rec["song"])
    groups[rec["category"]].append((title, p))

out_dir = DEST / "播放列表"
out_dir.mkdir(exist_ok=True)
for cat, items in groups.items():
    items.sort(key=lambda x: x[0].lower())
    lines = ["#EXTM3U"]
    for title, p in items:
        rel = Path("..") / p.relative_to(DEST)
        lines += ["#EXTINF:-1,%s" % title, str(rel).replace("\\", "/")]
    (out_dir / ("%s.m3u8" % cat)).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(cat, len(items))
