import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R

OUT = Path(r"D:\music\_research\resolve.json")

# index -> (query, song, artist, accept_low_name, category_override)
FIXES = {
    276: ("太阳照常升起 久石让", "太阳照常升起", "久石让", True, None),
    331: ("出埃及记 马克西姆", "出埃及记", "马克西姆", True, "经典老歌"),
}


def main():
    recs = json.load(open(OUT, encoding="utf-8"))
    for idx, (q, song, artist, allow_lang, cat) in FIXES.items():
        rec = recs[idx - 1]
        cands = R.search(q, 8)
        best, score, (ns, as_, ds) = R.pick(cands, song, artist, "", rec["duration"])
        print("#%d pick: %r - %r ns=%.2f as=%.2f ds=%.2f" % (
            idx, best and best["name"], best and best["artist"], ns, as_, ds))
        ok = best and as_ >= 0.55 and (
            ns >= 0.80 or (allow_lang and ds >= 0.85))
        if not ok:
            print("  REJECT -> bili")
            rec.update({"status": "bili", "match": None, "url": "",
                        "quality": "", "size": 0})
            continue
        hit = None
        for qual in ("flac", "320k"):
            hit = R.resolve_url(best["id"], qual)
            if hit:
                break
        if not hit:
            print("  NO URL -> bili")
            rec.update({"status": "bili", "match": None})
            continue
        rec.update({
            "song": song,
            "artist": artist,
            "match": best,
            "status": "ok",
            "quality": hit["level"],
            "url": hit["url"],
            "size": R.head_size(hit["url"]),
            "category": cat or R.category(best, rec["bili_title"], song, artist),
            "confidence": score,
            "name_sim": ns,
            "artist_sim": as_,
            "dur_sim": ds,
        })
        print("  OK %s %r %d bytes | %s" % (
            hit["level"], best["name"], rec["size"], rec["category"]))

    recs[143]["category"] = "欧美"
    json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved")


if __name__ == "__main__":
    main()
