import json
import re
import sys
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(r"D:\music")
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": "https://music.163.com/",
}

NOISE = [
    r"在百万豪装录音棚大声听", r"百万级装备试听", r"百万级装备听", r"百万豪装录音棚",
    r"百万级录音棚听", r"百万级录音棚", r"Hi[- ·]?Res", r"Hi-Res", r"无损音质", r"真无损",
    r"无损", r"4K", r"动态歌词", r"日推歌单", r"日推", r"歌单", r"纯音乐", r"纯音单曲",
    r"单曲推荐", r"音乐可视化", r"黑胶试听", r"试听", r"循环歌单", r"歌曲分享", r"音乐",
    r"第[一二三四五六七八九十百]+期", r"Lyrics", r"Official", r"MV", r"OP\d?|ED\d?",
]
NOISE_RE = re.compile("|".join(NOISE), re.I)


def clean_title(t):
    t = t.replace("\u00a0", " ")
    t = re.sub(r"[【\[（(「『][^】\]）)」』]{0,20}[】\]）)」』]", " ", t)
    t = NOISE_RE.sub(" ", t)
    t = re.sub(r"[|｜丨/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -—–~·,，.。!！?？\"'“”")
    return t


def extract(title):
    t = title.replace("\u00a0", " ")
    brackets = re.findall(r"[《「『]([^》」』]{1,80})[》」』]", t)
    song = brackets[0].strip() if brackets else None
    artist = None
    if song:
        idx = t.find(song)
        before = t[: max(0, idx - 1)]
        before = re.split(r"[|｜丨/【\[（(]", before)[-1]
        before = clean_title(before)
        before = re.sub(r"^[“\"'].*?[”\"']\s*", "", before)
        before = re.sub(r"(主题曲|片尾曲|片头曲|插曲|op|OP|OP\d+|BGM|开场音乐)$", "", before).strip(" -—–~")
        if 1 <= len(before) <= 30 and not re.search(r"[，。！？!?]", before):
            artist = before
    else:
        q = clean_title(t)
        q = re.sub(r"^[“\"'].*?[”\"']\s*", "", q)
        q = re.sub(r"[“\"'][^“\"']*[”\"']", " ", q)
        q = re.sub(r"\s+", " ", q).strip(" -—–~·")
        song = q
        m = re.match(r"^(.{1,40}?)\s+-\s+(.{1,40})$", q)
        if m:
            song = m.group(1).strip()
            artist = m.group(2).strip()
    return (song or clean_title(t)).strip(), (artist or "").strip()


def http_json(url, headers=None, data=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or UA, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def netease_search(q, limit=5):
    u = "https://music.163.com/api/search/get/web?s=%s&type=1&limit=%d&offset=0" % (
        urllib.parse.quote(q), limit)
    d = http_json(u)
    out = []
    for s in ((d.get("result") or {}).get("songs") or []):
        out.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "artist": "/".join(a.get("name", "") for a in s.get("artists") or []),
            "album": (s.get("album") or {}).get("name"),
            "duration": (s.get("duration") or 0) // 1000,
            "fee": s.get("fee"),
        })
    return out


def ratio(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def pick(cands, song, artist, dur):
    best, best_score = None, 0
    for c in cands:
        s = ratio(song, c["name"] or "")
        if artist:
            s += 0.35 * ratio(artist, c["artist"] or "")
        if dur and c["duration"]:
            s += 0.25 * max(0, 1 - abs(dur - c["duration"]) / 60)
        if s > best_score:
            best, best_score = c, s
    return best, best_score


def wy_flac(song_id):
    body = json.dumps({"source": "wy", "musicId": str(song_id), "quality": "flac"}).encode()
    req = urllib.request.Request(
        "https://c.wwwweb.top/music/url", data=body,
        headers={"Content-Type": "application/json", "User-Agent": "lx-music-desktop/2.10.1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
            return d.get("url") if d.get("code") == 200 else None
    except Exception as e:
        return None


def main():
    favs = json.load(open(ROOT / "_research" / "favorites.json", encoding="utf-8"))
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    for m in favs[:n]:
        song, artist = extract(m["title"])
        cands = netease_search(("%s %s" % (song, artist)).strip(), 5)
        best, score = pick(cands, song, artist, m["duration"])
        url = wy_flac(best["id"]) if best else None
        status = "FLAC" if url else "NO"
        print("[%s] %s | %s | %s | score=%.2f | fee=%s" % (
            status, song[:40], artist[:20],
            (best["name"] + " - " + best["artist"]) if best else "-", score,
            best["fee"] if best else "-"), flush=True)
        time.sleep(0.6)


if __name__ == "__main__":
    main()
