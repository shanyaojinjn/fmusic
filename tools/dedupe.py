import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\music")
RES = ROOT / "_research" / "resolve.json"
STATE = ROOT / "_research" / "download_state.json"


def main():
    recs = json.load(open(RES, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))
    groups = defaultdict(list)
    for k, st in sorted(state.items(), key=lambda kv: int(kv[0])):
        m = recs[int(k)].get("match") or {}
        if m.get("id") and st.get("file"):
            groups[m["id"]].append(k)

    for song_id, keys in groups.items():
        files = {k: Path(state[k]["file"]) for k in keys}
        existing = {k: p for k, p in files.items() if p.exists()}
        if len(existing) < 2:
            for k in keys:
                if k not in existing and existing:
                    state[k]["file"] = str(next(iter(existing.values())))
            continue
        keep_k = min(existing, key=lambda k: int(k))
        keep = existing[keep_k]
        for k, p in existing.items():
            if p == keep:
                state[k]["file"] = str(keep)
                continue
            if abs(p.stat().st_size - keep.stat().st_size) <= max(1024, keep.stat().st_size * 0.01):
                p.unlink()
                state[k]["file"] = str(keep)
                print("DEDUPE", int(k) + 1, p.name, "->", keep.name)
            else:
                print("KEEP BOTH", int(k) + 1, p.stat().st_size, keep.stat().st_size, p.name)

    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
