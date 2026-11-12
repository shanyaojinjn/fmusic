import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R

ROOT = Path(r"D:\music")
RES = ROOT / "_research" / "resolve.json"
STATE = ROOT / "_research" / "download_state.json"

FIX = {
    52: {
        "query": "天空之城 久石譲 天空の城ラピュタ",
        "song": "天空之城", "artist": "久石让", "pick_id": 442682,
        "category": "经典老歌",
    },
    107: {
        "query": "As It Was Harry Styles",
        "song": "As It Was", "artist": "Harry Styles", "pick_id": 1933791692,
        "category": "欧美",
    },
}


def main():
    recs = json.load(open(RES, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))
    for idx, spec in FIX.items():
        rec = recs[idx - 1]
        cands = R.search(spec["query"], 8)
        best = next((c for c in cands if c["id"] == spec["pick_id"]), None)
        if not best:
            print(idx, "not found")
            continue
        levels = ["master", "flac", "320k"] if spec["category"] == "经典老歌" else ["flac", "320k"]
        hit = None
        for q in levels:
            hit = R.resolve_url(best["id"], q)
            if hit:
                break
        if not hit:
            print(idx, "no url")
            continue
        old = state.get(str(idx - 1), {})
        if old.get("file") and Path(old["file"]).exists():
            Path(old["file"]).unlink()
            print("removed", old["file"])
        rec.update({
            "song": spec["song"], "artist": spec["artist"], "match": best,
            "status": "ok", "quality": hit["level"], "url": hit["url"],
            "size": R.head_size(hit["url"]), "category": spec["category"],
            "confidence": 0.95, "name_sim": 0.0, "artist_sim": 0.0,
            "dur_sim": 0.5,
        })
        state.pop(str(idx - 1), None)
        print(idx, "->", best["name"], best["artist"], hit["level"])
    json.dump(recs, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
