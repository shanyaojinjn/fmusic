import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R

OUT = Path(r"D:\music\_research\resolve.json")

# index -> (query, song, artist)
FIXES = {
    138: ("That Girl Olly Murs", "That Girl", "Olly Murs"),
    144: ("Nice Boys TEMPOREX", "Nice Boys", "TEMPOREX"),
    205: ("Move Up Lost Gravity Mr. Polska", "Move Up (Lost Gravity)", "Mr. Polska"),
    276: ("太阳照常升起 久石让", "太阳照常升起", "久石让"),
    331: ("出埃及记 马克西姆", "出埃及记", "马克西姆"),
    316: ("White Cherry Melancholy", "Melancholy", "White Cherry"),
}


def main():
    recs = json.load(open(OUT, encoding="utf-8"))
    for idx, (q, song, artist) in FIXES.items():
        rec = recs[idx - 1]
        try:
            cands = R.search(q, 8)
        except Exception as e:
            print("#%d search failed: %s" % (idx, e))
            continue
        best, score, (ns, as_, ds) = R.pick(cands, song, artist, "", rec["duration"])
        print("#%d %s" % (idx, rec["bili_title"][:60]))
        print("  pick: %r - %r  ns=%.2f as=%.2f ds=%.2f score=%.2f" % (
            best and best["name"], best and best["artist"], ns, as_, ds, score))
        if not best or as_ < 0.55 or ns < 0.80:
            print("  REJECT -> bili")
            rec["status"] = "bili"
            rec["match"] = None
            rec["url"] = ""
            rec["quality"] = ""
            rec["size"] = 0
            continue
        hit = None
        for qual in ("flac", "320k"):
            hit = R.resolve_url(best["id"], qual)
            if hit:
                break
        if not hit:
            print("  NO URL -> bili")
            rec["status"] = "bili"
            rec["match"] = None
            continue
        rec.update({
            "song": song,
            "artist": artist,
            "match": best,
            "status": "ok",
            "quality": hit["level"],
            "url": hit["url"],
            "size": R.head_size(hit["url"]),
            "category": R.category(best, rec["bili_title"], song, artist),
            "confidence": score,
            "name_sim": ns,
            "artist_sim": as_,
            "dur_sim": ds,
        })
        print("  OK %s %r %d bytes | %s" % (
            hit["level"], best["name"], rec["size"], rec["category"]))
    json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved")


if __name__ == "__main__":
    main()
