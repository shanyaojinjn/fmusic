import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R

ROOT = Path(r"D:\music")
recs = json.load(open(ROOT / "_research" / "resolve.json", encoding="utf-8"))
state = json.load(open(ROOT / "_research" / "download_state.json", encoding="utf-8"))

targets = [int(k) for k, v in state.items() if "未知歌手" in (v.get("file") or "")]
targets.sort()

out = []
for k in targets:
    r = recs[k]
    url = "https://api.bilibili.com/x/web-interface/view?bvid=%s" % r["bvid"]
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": R.UA_STR, "Referer": "https://www.bilibili.com/"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            d = json.loads(resp.read().decode("utf-8", "ignore"))
        data = d.get("data") or {}
        out.append({
            "key": k,
            "bvid": r["bvid"],
            "title": r["bili_title"],
            "desc": (data.get("desc") or "").strip(),
            "tags": [t.get("tag_name") for t in (data.get("tags") or [])],
            "owner": (data.get("owner") or {}).get("name", ""),
            "duration": data.get("duration", 0),
        })
        print(k, "OK", (data.get("desc") or "")[:60].replace("\n", " "))
    except Exception as e:
        print(k, "FAIL", e)
        out.append({"key": k, "bvid": r["bvid"], "title": r["bili_title"],
                    "desc": "", "tags": [], "owner": "", "duration": 0})
    time.sleep(0.8)

(ROOT / "_research" / "bili_info.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved", len(out))
