# -*- coding: utf-8 -*-
"""Stage 1: resolve every Bilibili favorite to a high-quality audio source.

Writes _research/resolve.json. No audio is downloaded here.
"""
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(r"D:\music")
OUT = ROOT / "_research" / "resolve.json"
UA_STR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HDR = {"User-Agent": UA_STR, "Referer": "https://music.163.com/"}

NOISE = [
    r"在百万豪装录音棚大声听", r"百万级装备试听", r"百万级装备听", r"百万豪装录音棚",
    r"百万级录音棚听", r"百万级录音棚", r"Hi[- ·]?Res", r"无损音质", r"真无损",
    r"无损", r"4K", r"动态歌词", r"日推歌单", r"日推", r"歌单", r"纯音乐", r"纯音单曲",
    r"单曲推荐", r"音乐可视化", r"黑胶试听", r"试听", r"循环歌单", r"歌曲分享", r"音乐",
    r"第[一二三四五六七八九十百]+期", r"Lyrics", r"Official", r"MV", r"BGM",
]
NOISE_RE = re.compile("|".join(NOISE), re.I)

CLASSIC_ARTISTS = [
    "罗大佑", "李宗盛", "邓丽君", "张国荣", "谭咏麟", "梅艳芳", "beyond", "草蜢",
    "陈慧娴", "李克勤", "张学友", "刘德华", "王杰", "陈百强", "林子祥", "叶倩文",
    "关淑怡", "王菲", "那英", "齐秦", "童安格", "张雨生", "苏芮", "蔡琴", "费玉清",
    "周华健", "赵传", "黄莺莺", "潘越云", "陈淑桦", "辛晓琪", "张信哲", "邰正宵",
    "巫启贤", "伍佰", "张宇", "任贤齐", "郑智化", "小虎队", "孟庭苇", "叶丽仪",
    "徐小凤", "罗文", "甄妮", "许冠杰", "中森明菜", "山下达郎", "山下達郎", "杏里",
    "亜蘭知子", "亚兰知子", "中原めいこ", "中原芽衣子", "竹内まりや", "松任谷由実",
    "山口百恵", "山口百惠", "美空ひばり", "carpenters", "pink floyd", "adele",
    "bruno mars", "green day", "lenka", "jody", "patti austin",
]
GAME_WORDS = ["塞尔达", "奥特曼", "ウルトラマン", "盖亚", "戴拿", "迪迦", "崩坏", "星穹铁道",
              "蔚蓝档案", "原神", "明日方舟", "游戏", "动画", "动漫", "主题曲", "ソードアート"]


def clean_title(t):
    t = unicodedata.normalize("NFKC", t).replace("\u00a0", " ").replace("　", " ")
    t = re.sub(r"[【\[（(「『][^】\]）)」』]{0,20}[】\]）)」』]", " ", t)
    t = NOISE_RE.sub(" ", t)
    t = re.sub(r"[|｜丨/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -—–~·,，.。!！?？\"'“”》」』】）)]}")
    return t


def seg_score(s):
    latin = len(re.findall(r"[A-Za-z]", s))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", s))
    return latin - 1.5 * cjk - 0.05 * len(s)


def latin_runs(s):
    out = []
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9'&.,\- ]{2,60}", s):
        r = m.group().strip(" -—–,.")
        if len(re.findall(r"[A-Za-z]", r)) >= 3:
            out.append(r)
    return out


def latin_words(s):
    return len(re.findall(r"[A-Za-z][A-Za-z'&.]*", s))


def dash_pick(s):
    """Split 'A - B' into (song_side, artist_side) using word-count heuristics."""
    m = re.match(r"^(.{1,60}?)\s+-\s+(.{1,60})$", s.strip())
    if not m:
        return None
    l, r = m.group(1).strip(), m.group(2).strip()
    wl, wr = latin_words(l), latin_words(r)
    if wl == 0:
        return r, l
    if wr == 0:
        return l, r
    if re.search(r"[\u4e00-\u9fff]", r) and not re.search(r"[\u4e00-\u9fff]", l):
        return l, r
    if "," in r and "," not in l:
        return l, r
    if wr <= 1:
        return l, r
    return (l, r) if wl >= wr else (r, l)


def latin_part(b):
    if not re.search(r"[A-Za-z]\s+[一-鿿]|[一-鿿]\s+[A-Za-z]", b):
        return b
    toks = [x for x in re.split(r"\s+", b) if re.search(r"[A-Za-z]", x)]
    return " ".join(toks).strip(" -—–~·")


def bracket_ok(b):
    if len(b) > 60 or b.count("/") >= 2:
        return False
    if re.search(r"(奥特曼|战士)$", b) and len(b) <= 8:
        return False
    if re.search(r"游戏|动画|动漫|主题曲|音乐|歌单|哪个|危机|改编|蔚蓝档案|星穹铁道|崩坏", b):
        return False
    if re.search(r"神曲|小曲|复古|合成器|浪潮|精选|必听|纯音|配乐|合集|金曲|高能|神级|ost", b, re.I):
        return False
    if not re.search(r"[A-Za-z]", b) and len(b) > 14:
        return False
    if b[-1] in "！!？?":
        return False
    return True


def extract(title):
    """Return (song, artist, alt_song). alt_song is the other side of a dash pair."""
    t = unicodedata.normalize("NFKC", title).replace("\u00a0", " ").replace("　", " ")
    raw = re.findall(r"[《「『]([^》」』]{1,80})[》」』]", t)
    brackets = [b.strip() for b in raw
                if clean_title(b) and not NOISE_RE.fullmatch(b.strip())
                and len(clean_title(b)) >= 1]

    base = re.sub(r"[《「『][^》」』]{0,80}[》」』]", " ", t)
    base = re.sub(r"[（(][^）)]{0,40}[）)]", " ", base)
    base = clean_title(base)
    base = re.sub(r"^[“\"'].*?[”\"']\s*", "", base)
    base = re.sub(r"[“\"'][^“\"']*[”\"']", " ", base)
    base = re.sub(r"\s+", " ", base).strip(" -—–~·,，.。")

    curated = [b for b in brackets if bracket_ok(b)]
    song, alt, artist = "", "", ""
    if curated:
        latin_bs = [x for x in curated if re.search(r"[A-Za-z]", x)]
        b = (latin_bs or curated)[-1]
        after = clean_title(t[t.find(b) + len(b):])
        runs = latin_runs(after)
        if runs and len(b) <= 8 and len(runs[0]) >= 4:
            artist = b
            pick = dash_pick(runs[0])
            if pick:
                song, alt = pick
            else:
                song = runs[0]
        else:
            song = latin_part(b) or b
    if not song and not curated:
        pick = dash_pick(base)
        if pick:
            song, alt = pick
            if re.search(r"[\u4e00-\u9fff]", song):
                runs = latin_runs(song)
                if runs:
                    song = max(runs, key=seg_score)
        elif re.search(r"[\u4e00-\u9fff]", base):
            segs = [s for s in re.split(r"\s+", base) if s]
            cjk_segs = [s for s in segs
                        if re.fullmatch(r"[\u4e00-\u9fff·]+", s) and 2 <= len(s) <= 12]
            latin_segs = [s for s in segs if re.search(r"[A-Za-z]", s)]
            if cjk_segs and latin_segs and len(segs) <= 3:
                song, artist = cjk_segs[0], latin_segs[0]
    if not song:
        runs = latin_runs(base)
        song = runs[0] if runs else base

    if not artist and alt and len(alt) <= 30 and not re.search(r"[，。！？!?]", alt):
        artist = alt
    if not artist:
        src = curated[0] if curated else ""
        idx = t.find(src) if src else -1
        if idx >= 0:
            before = t[: max(0, idx - 1)]
            before = re.split(r"[|｜丨/【\[（(]", before)[-1]
            before = clean_title(before)
            before = re.sub(r"(主题曲|片尾曲|片头曲|插曲|op|OP|OP\d+|BGM|开场音乐)$", "", before)
            before = before.strip(" -—–~")
            if 1 <= len(before) <= 30 and not re.search(r"[，。！？!?]", before):
                artist = before
            tail = clean_title(t[idx + len(src):])
            tail = re.sub(r"^(主题曲|片尾曲|片头曲|插曲|op|OP|OP\d*|BGM)", " ", tail).strip(" -—–~·")
            if not artist and 1 <= len(tail) <= 30 and not re.search(r"[，。！？!?]", tail):
                artist = tail
    return song.strip(), artist.strip(), alt.strip()


def http_json(url, data=None, timeout=25, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def search(q, limit=8):
    u = ("https://music.163.com/api/cloudsearch/pc?s=%s&type=1&limit=%d&offset=0"
         % (urllib.parse.quote(q), limit))
    d = http_json(u)
    out = []
    for s in ((d.get("result") or {}).get("songs") or []):
        al = s.get("al") or {}
        out.append({
            "id": s.get("id"),
            "name": s.get("name") or "",
            "alia": [x for x in (s.get("alia") or []) if x],
            "artist": "/".join(a.get("name", "") for a in (s.get("ar") or [])),
            "album": al.get("name") or "",
            "cover": al.get("picUrl") or "",
            "duration": (s.get("dt") or 0) // 1000,
            "fee": s.get("fee"),
            "year": time.gmtime(s["publishTime"] / 1000).tm_year
            if 0 < (s.get("publishTime") or 0) < 4e12 else 0,
        })
    return out


def norm(s):
    s = re.sub(r"[\s\-—_·,，.。!！?？'\"“”()（）\[\]【】]", "", s or "")
    return s.lower()


def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def name_score(c, song, alt):
    names = [c["name"]] + c["alia"]
    for n in list(names):
        names += [x.strip() for x in re.split(r"\s*/\s*|\s+&\s+|\s*[~～]\s*", n) if len(x.strip()) >= 2]
        bare = re.sub(r"\s*[（(\[【][^）)\]】]*[）)\]】]", "", n).strip()
        if bare and bare != n:
            names.append(bare)
    song = re.sub(r"\s*[（(\[【][^）)\]】]*[）)\]】]", "", song).strip()
    best = max(sim(song, n) for n in names)
    if alt:
        best = max(best, max(sim(alt, n) for n in names))
    return best


def artist_sim(artist, cand):
    parts = [artist] + [x.strip() for x in re.split(r"[,&/、]", artist) if x.strip()]
    return max(sim(p, cand) for p in parts)


def pick(cands, song, artist, alt, dur):
    best, best_score, best_parts = None, 0.0, (0, 0, 0)
    for rank, c in enumerate(cands):
        ns = name_score(c, song, alt)
        as_ = artist_sim(artist, c["artist"]) if artist else 0.5
        ds = max(0.0, 1 - abs(dur - c["duration"]) / 90) if (dur and c["duration"]) else 0.5
        if artist:
            score = 0.60 * ns + 0.25 * as_ + 0.15 * ds
        else:
            score = 0.55 * ns + 0.45 * ds
        score += 0.02 - 0.02 * min(rank, 5)
        if rank and re.search(r"翻唱|cover|COVERS", c["album"] + c["artist"], re.I):
            score -= 0.10
        if score > best_score:
            best, best_score, best_parts = c, score, (ns, as_, ds)
    return best, best_score, best_parts


QUALITY_CACHE = {}


def resolve_url(song_id, quality):
    key = (song_id, quality)
    if key in QUALITY_CACHE:
        return QUALITY_CACHE[key]
    body = json.dumps({"source": "wy", "musicId": str(song_id),
                       "quality": quality}).encode()
    res = None
    try:
        d = http_json("https://c.wwwweb.top/music/url", data=body, timeout=25,
                      headers={"Content-Type": "application/json",
                               "User-Agent": "lx-music-desktop/2.10.1"})
        if d.get("code") == 200 and d.get("url"):
            res = {"url": d["url"], "level": d.get("level") or quality}
    except Exception:
        res = None
    QUALITY_CACHE[key] = res
    return res


def head_size(url):
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": UA_STR})
        with urllib.request.urlopen(req, timeout=25) as r:
            n = r.headers.get("Content-Length")
            return int(n) if n else 0
    except Exception:
        return 0


WORK_WORDS = ["奥特曼", "ウルトラマン", "盖亚", "戴拿", "迪迦", "塞尔达", "游戏", "动画",
              "动漫", "日推", "歌单", "纯音乐", "后摇", "民谣", "音乐", "最好听", "金曲",
              "神曲", "小曲", "蒸汽波", "翻自", "经典", "必听", "合集", "推荐", "纯音",
              "萨克斯", "钢琴", "片尾", "插曲", "主题曲", "完整版", "降调", "dj"]


def artist_ok(artist):
    if not artist or len(artist) < 2:
        return ""
    if any(w in artist for w in WORK_WORDS):
        return ""
    if NOISE_RE.search(artist):
        return ""
    if re.fullmatch(r"(?i)flac|wav|mp3|ape|alac|m4a|hi-?res|dsd", artist):
        return ""
    if not re.search(r"[A-Za-z]", artist) and (
            len(artist) > 6 or re.search(r"\s", artist)):
        return ""
    artist = re.sub(r"[^\w\s\-&.,'·（）()]", "", artist).strip()
    return artist


def category(match, title, song, artist):
    m_artist = (match or {}).get("artist") or ""
    year = (match or {}).get("year") or 0
    album = (match or {}).get("album") or ""
    hay = (title + " " + album).lower()
    if any(w.lower() in hay for w in GAME_WORDS):
        return "游戏·影视·BGM"
    if any(a in (artist + m_artist).lower() for a in CLASSIC_ARTISTS):
        return "经典老歌"
    if 1950 <= year <= 2005:
        return "经典老歌"
    text = (match["name"] if match else song) + m_artist
    if re.search(r"[\u3040-\u30ff]", text):
        return "日语·ACG"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "华语流行"
    return "欧美"


def main():
    global OUT
    favs = json.load(open(ROOT / "_research" / "favorites.json", encoding="utf-8"))
    if len(sys.argv) > 1:
        OUT = ROOT / "_research" / ("resolve_sample.json" if sys.argv[1] == "sample"
                                    else "resolve.json")
        if sys.argv[1] == "sample":
            favs = favs[:30]
    results = []
    if OUT.exists():
        results = json.load(open(OUT, encoding="utf-8"))
    done = {r["bvid"] for r in results}
    start = time.time()

    for i, m in enumerate(favs):
        if m["bvid"] in done:
            continue
        song, artist, alt = extract(m["title"])
        artist = artist_ok(artist)
        queries = []
        if artist:
            queries.append("%s %s" % (song, artist))
        queries.append(song)
        if alt:
            queries.append("%s %s" % (alt, artist) if artist else alt)

        cands = []
        seen = set()
        for q in queries:
            for c in search(q):
                if c["id"] not in seen:
                    seen.add(c["id"])
                    cands.append(c)
            time.sleep(0.35)
        best, score, (ns, as_, ds) = pick(cands, song, artist, alt, m["duration"])

        rec = {
            "index": i,
            "bvid": m["bvid"],
            "page": m.get("page", 1),
            "bili_title": m["title"],
            "duration": m["duration"],
            "song": song,
            "artist": artist,
            "alt": alt,
            "match": None,
            "status": "bili",
            "quality": "",
            "url": "",
            "size": 0,
            "category": "",
            "confidence": round(score, 3),
            "name_sim": round(ns, 3),
            "artist_sim": round(as_, 3),
            "dur_sim": round(ds, 3),
        }

        accepted = bool(best) and ns >= 0.85 and (
            not artist or as_ >= 0.55 or (ns >= 0.97 and ds >= 0.5))
        if accepted:
            is_classic = (
                any(a in (best["artist"] + artist).lower() for a in CLASSIC_ARTISTS)
                or (best["year"] and best["year"] <= 2005)
            )
            levels = ["master", "flac", "320k"] if is_classic else ["flac", "320k"]
            got = None
            for q in levels:
                got = resolve_url(best["id"], q)
                if got:
                    break
                time.sleep(0.4)
            if got:
                size = head_size(got["url"])
                if size == 0 or size > 300 * 1024:
                    rec.update({
                        "match": best,
                        "status": "ok",
                        "quality": got["level"],
                        "url": got["url"],
                        "size": size,
                    })
            else:
                rec["status"] = "no_url"
                rec["match"] = best

        rec["category"] = category(rec["match"], m["title"], song, artist)
        results.append(rec)
        results.sort(key=lambda r: r["index"])
        if len(results) % 5 == 0:
            OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        print("[%3d/%d] %s %s | %s | %s" % (
            i + 1, len(favs), rec["status"], rec["category"],
            (best["name"] + " - " + best["artist"]) if rec["match"] else "-",
            m["title"][:40]), flush=True)
        time.sleep(0.7)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for r in results if r["status"] == "ok")
    print("DONE %d records, %d ok, %.1f min" % (len(results), ok, (time.time() - start) / 60))


if __name__ == "__main__":
    main()
