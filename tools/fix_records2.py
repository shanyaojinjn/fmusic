import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R

ROOT = Path(r"D:\music")
RES = ROOT / "_research" / "resolve.json"
STATE = ROOT / "_research" / "download_state.json"

FIX = {
    10: {"query": "明日へ ウルトラマンダイナ 矢野立美", "pick_id": 28606406,
         "song": "明日へ…", "artist": "矢野立美"},
    300: {"query": "不怕 赵蓓 赵蕾 CD版", "pick_id": 1992762997,
          "song": "不怕 (CD版)", "artist": "赵蓓/赵蕾"},
    104: {"query": "", "pick_id": None, "song": None, "artist": None},
}


def main():
    recs = json.load(open(RES, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))
    for idx, spec in FIX.items():
        key = str(idx - 1)
        old = state.get(key, {})
        if old.get("file") and Path(old["file"]).exists():
            Path(old["file"]).unlink()
            print("removed", old["file"])
        state.pop(key, None)
        if spec["pick_id"] is None:
            continue
        cands = R.search(spec["query"], 8)
        best = next((c for c in cands if c["id"] == spec["pick_id"]), None)
        if not best:
            print(idx, "not found")
            continue
        hit = None
        for q in ("flac", "320k"):
            hit = R.resolve_url(best["id"], q)
            if hit:
                break
        rec = recs[idx - 1]
        rec.update({
            "song": spec["song"], "artist": spec["artist"], "match": best,
            "status": "ok" if hit else "bili",
            "quality": hit["level"] if hit else "",
            "url": hit["url"] if hit else "",
            "size": R.head_size(hit["url"]) if hit else 0,
            "category": R.category(best, rec["bili_title"], spec["song"], spec["artist"]),
            "confidence": 0.9, "name_sim": 0.0, "artist_sim": 0.0, "dur_sim": 0.8,
        })
        print(idx, "->", best["name"], best["artist"], hit and hit["level"])
    json.dump(recs, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
