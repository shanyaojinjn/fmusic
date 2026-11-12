# -*- coding: utf-8 -*-
"""Build downloads/_manifest.csv from download_state.json + resolve.json."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\music")
OUT = ROOT / "downloads" / "_manifest.csv"


def main():
    recs = json.load(open(ROOT / "_research" / "resolve.json", encoding="utf-8"))
    by_index = {str(r["index"]): r for r in recs}
    state = json.load(open(ROOT / "_research" / "download_state.json",
                           encoding="utf-8"))

    rows = []
    for key, st in sorted(state.items(), key=lambda kv: int(kv[0])):
        rec = by_index.get(key)
        if not rec:
            continue
        path = Path(st.get("file") or "")
        m = rec.get("match") or {}
        src = st.get("source") or ""
        if src == "existing" or not src:
            src = "bilibili" if (st.get("quality") or "") == "30280" else "netease"
        rows.append({
            "序号": rec["index"] + 1,
            "分类": path.parent.name if path.parent.name else rec["category"],
            "歌名": m.get("name") or rec["song"],
            "歌手": m.get("artist") or rec["artist"],
            "专辑": m.get("album") or "",
            "来源": {"netease": "网易云", "bilibili": "B站"}.get(src, src),
            "音质": st.get("quality") or "",
            "格式": path.suffix.lstrip(".").upper(),
            "大小MB": round((st.get("size") or 0) / 1048576, 2) if not path.exists() else round(path.stat().st_size / 1048576, 2),
            "时长": "%d:%02d" % (rec["duration"] // 60, rec["duration"] % 60),
            "文件名": path.name,
            "B站原视频": ("https://www.bilibili.com/video/%s" % rec["bvid"])
            if rec.get("bvid") else "（手动追加）",
            "状态": st.get("status"),
            "备注": st.get("error", ""),
        })

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r["状态"] == "ok"]
    print("rows=%d ok=%d" % (len(rows), len(ok)))
    print("size GB=%.2f" % (sum(r["大小MB"] for r in ok) / 1024))
    print("source", Counter(r["来源"] for r in ok))
    print("category", Counter(r["分类"] for r in ok))
    bad = [r for r in rows if r["状态"] != "ok"]
    for r in bad:
        print("FAIL", r["序号"], r["歌名"], r["备注"][:120])


if __name__ == "__main__":
    main()
