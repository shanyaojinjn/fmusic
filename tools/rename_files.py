import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import download_all as D

ROOT = Path(r"D:\music")
RES = ROOT / "_research" / "resolve.json"
STATE = ROOT / "_research" / "download_state.json"


def main():
    recs = json.load(open(RES, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))
    for key, st in state.items():
        f = st.get("file")
        if not f:
            continue
        cur = Path(f)
        if not cur.exists():
            continue
        want = D.target_path(recs[int(key)]).with_suffix(cur.suffix)
        if want == cur:
            continue
        if want.exists():
            print("SKIP exists", want.name)
            continue
        cur.rename(want)
        st["file"] = str(want)
        print("RENAME", cur.name, "->", want.name)
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
