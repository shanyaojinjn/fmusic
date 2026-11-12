# -*- coding: utf-8 -*-
"""Scrape and embed cover art, lyrics, artist/album tags for the library."""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, COMM, ID3, TALB, TDRC, TIT2, TPE1, USLT
from mutagen.mp4 import MP4, MP4Cover
from mutagen.wave import WAVE

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R

ROOT = Path(r"D:\music")
CACHE = ROOT / "_research" / "tag_cache"
LYRIC_DIR = CACHE / "lyrics"
COVER_DIR = CACHE / "covers"
LYRIC_DIR.mkdir(parents=True, exist_ok=True)
COVER_DIR.mkdir(parents=True, exist_ok=True)

recs = json.load(open(ROOT / "_research" / "resolve.json", encoding="utf-8"))
state = json.load(open(ROOT / "_research" / "download_state.json", encoding="utf-8"))
bili_info = {}
bi_path = ROOT / "_research" / "bili_info.json"
if bi_path.exists():
    for x in json.load(open(bi_path, encoding="utf-8")):
        bili_info[x["bvid"]] = x

HDR = {"User-Agent": R.UA_STR, "Referer": "https://www.bilibili.com/"}


def http_bytes(url, referer=None):
    h = {"User-Agent": R.UA_STR}
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def bili_pic(bvid):
    f = COVER_DIR / ("bili-%s.jpg" % bvid)
    if f.exists() and f.stat().st_size > 1000:
        return f.read_bytes()
    try:
        d = R.http_json("https://api.bilibili.com/x/web-interface/view?bvid=%s" % bvid,
                        headers=HDR)
        pic = ((d.get("data") or {}).get("pic") or "")
    except Exception:
        pic = ""
    if not pic:
        return b""
    if "@" not in pic:
        pic += "@600w_600h.jpg"
    try:
        data = http_bytes(pic, "https://www.bilibili.com/")
    except Exception:
        return b""
    if len(data) > 1000:
        f.write_bytes(data)
        return data
    return b""


def cover_bytes(rec):
    m = rec.get("match") or {}
    url = m.get("cover") or ""
    if url:
        if "music.126.net" in url and "?param=" not in url:
            url += "?param=600y600"
        f = COVER_DIR / ("wy-%s.jpg" % m["id"])
        if f.exists() and f.stat().st_size > 1000:
            return f.read_bytes()
        try:
            data = http_bytes(url, "https://music.163.com/")
            if len(data) > 1000:
                f.write_bytes(data)
                return data
        except Exception:
            pass
    return bili_pic(rec["bvid"])


def lyric_text(rec):
    m = rec.get("match") or {}
    if not m.get("id"):
        return ""
    f = LYRIC_DIR / ("%s.lrc" % m["id"])
    if f.exists():
        return f.read_text(encoding="utf-8")
    text = ""
    try:
        d = R.http_json("https://music.163.com/api/song/lyric?id=%s&lv=-1&kv=-1&tv=-1"
                        % m["id"], headers={"User-Agent": R.UA_STR,
                                            "Referer": "https://music.163.com/"})
        text = ((d.get("lrc") or {}).get("lyric") or "").strip()
        if not text or text.lower().startswith("[00:00.000] 纯音乐"):
            text = ""
    except Exception:
        text = ""
    f.write_text(text, encoding="utf-8")
    return text


def tags_for(rec):
    m = rec.get("match") or {}
    title = (m.get("name") or rec["song"] or "").strip()
    artist = (m.get("artist") or rec["artist"] or "").strip()
    album = (m.get("album") or "").strip()
    if not album:
        album = "B站收藏"
    year = str(m.get("year") or "")
    src = "网易云音乐" if m else "B站"
    comment = "来源: %s | B站: https://www.bilibili.com/video/%s" % (src, rec["bvid"])
    return title, artist, album, year, comment


def embed(path, title, artist, album, year, comment, lyric, cover):
    ext = path.suffix.lower()
    if ext == ".flac":
        a = FLAC(str(path))
        a["title"] = title
        a["artist"] = artist
        a["album"] = album
        if year:
            a["date"] = year
        a["comment"] = comment
        if lyric:
            a["lyrics"] = lyric
        a.clear_pictures()
        if cover:
            pic = Picture()
            pic.type = 3
            pic.mime = "image/jpeg"
            pic.desc = "Cover"
            pic.data = cover
            a.add_picture(pic)
        a.save()
    elif ext == ".mp3":
        try:
            a = ID3(str(path))
        except Exception:
            a = ID3()
        a.delall("TIT2"); a.delall("TPE1"); a.delall("TALB")
        a.delall("TDRC"); a.delall("COMM"); a.delall("USLT"); a.delall("APIC")
        a.add(TIT2(encoding=3, text=title))
        a.add(TPE1(encoding=3, text=artist))
        a.add(TALB(encoding=3, text=album))
        if year:
            a.add(TDRC(encoding=3, text=year))
        a.add(COMM(encoding=3, lang="chi", desc="", text=comment))
        if lyric:
            a.add(USLT(encoding=3, lang="chi", desc="", text=lyric))
        if cover:
            a.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover))
        a.save(str(path), v2_version=3)
    elif ext in (".m4a", ".mp4"):
        a = MP4(str(path))
        a["\xa9nam"] = title
        a["\xa9ART"] = artist
        a["\xa9alb"] = album
        if year:
            a["\xa9day"] = year
        a["\xa9cmt"] = comment
        if lyric:
            a["\xa9lyr"] = lyric
        if cover:
            a["covr"] = [MP4Cover(cover, imageformat=MP4Cover.FORMAT_JPEG)]
        a.save()


def main():
    seen = set()
    stats = {"files": 0, "cover": 0, "lyric": 0, "fail": 0}
    for k, st in sorted(state.items(), key=lambda kv: int(kv[0])):
        f = st.get("file")
        if not f or f in seen:
            continue
        seen.add(f)
        p = Path(f)
        if not p.exists():
            continue
        rec = recs[int(k)]
        title, artist, album, year, comment = tags_for(rec)
        cover = cover_bytes(rec)
        lyric = lyric_text(rec)
        if lyric:
            p.with_suffix(".lrc").write_text(lyric + "\n", encoding="utf-8")
        try:
            embed(p, title, artist, album, year, comment, lyric, cover)
            stats["files"] += 1
            stats["cover"] += bool(cover)
            stats["lyric"] += bool(lyric)
        except Exception as e:
            stats["fail"] += 1
            print("FAIL", p.name, e)
        time.sleep(0.1)
    print(stats)


if __name__ == "__main__":
    main()
