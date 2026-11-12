# -*- coding: utf-8 -*-
"""Stage 2: download resolved audio into categorized folders.

Reads _research/resolve.json, re-requests fresh URLs, falls back to Bilibili
audio when the music-platform route fails. Resumable.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resolve_all as R

ROOT = Path(r"D:\music")
DEST = ROOT / "downloads"
STATE = ROOT / "_research" / "download_state.json"
BBDOWN = ROOT / "bbdown"
YTDLP = BBDOWN / "yt-dlp.exe"
FFMPEG = BBDOWN / "ffmpeg.exe"
COOKIES = BBDOWN / "cookies.txt"

BAD = re.compile(r'[\\/:*?"<>|\r\n\t]')


def safe(s, limit=120):
    s = BAD.sub(" ", s).replace("..", " ")
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s[:limit].strip(" .") or "untitled"


def target_path(rec):
    m = rec.get("match") or {}
    song = (m.get("name") or rec["song"]).strip()
    artist = (m.get("artist") or rec["artist"]).strip()
    if not m and (rec["song"] or rec["artist"]):
        song = rec["song"].strip() or song
        artist = rec["artist"].strip() or artist
    if not artist:
        artist = "未知歌手"
    base = safe("%s - %s" % (artist, song))
    folder = DEST / safe(rec["category"], 40)
    folder.mkdir(parents=True, exist_ok=True)
    ext = ".flac" if "flac" in (rec.get("quality") or "") else ".mp3"
    if rec.get("quality") == "master":
        ext = ".flac"
    return folder / (base + ext)


def sniff_ext(head):
    if head[:4] == b"fLaC":
        return ".flac"
    if head[:4] == b"OggS":
        return ".ogg"
    if head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ".mp3"
    if head[4:8] == b"ftyp":
        return ".m4a"
    if head[:4] == b"RIFF":
        return ".wav"
    return ""


def download(url, path, timeout=300):
    tmp = path.with_suffix(path.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": R.UA_STR})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1024 * 256)
    size = tmp.stat().st_size
    if size < 100 * 1024:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("file too small")
    with open(tmp, "rb") as f:
        ext = sniff_ext(f.read(12))
    if ext:
        path = path.with_suffix(ext)
    tmp.replace(path)
    return path, size


def fresh_url(rec):
    m = rec.get("match") or {}
    if not m.get("id"):
        return None
    levels = [rec.get("quality") or "flac", "flac", "320k"]
    seen = set()
    for q in levels:
        if q in seen:
            continue
        seen.add(q)
        got = R.resolve_url(m["id"], q)
        if got:
            return got
        time.sleep(0.5)
    return None


def bili_audio(rec, path):
    url = "https://www.bilibili.com/video/%s?p=%s" % (rec["bvid"], rec.get("page", 1))
    tmpl = str(path.with_suffix("")) + ".%(ext)s"
    cmd = [str(YTDLP), "--cookies", str(COOKIES),
           "--ffmpeg-location", str(BBDOWN),
           "-f", "bestaudio[format_id=30280]/bestaudio",
           "--no-playlist", "--no-warnings", "--quiet",
           "-o", tmpl, url]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="ignore", timeout=600)
    files = [f for f in path.parent.glob(path.stem + ".*")
             if f.suffix in (".m4a", ".aac", ".mp3", ".flac", ".opus", ".webm")]
    if files:
        return max(files, key=lambda f: f.stat().st_size)
    raise RuntimeError("yt-dlp failed: " + (p.stderr or "")[-300:])


def main():
    recs = json.load(open(ROOT / "_research" / "resolve.json", encoding="utf-8"))
    state = {}
    if STATE.exists():
        state = json.load(open(STATE, encoding="utf-8"))

    for rec in recs:
        key = str(rec["index"])
        done = state.get(key)
        if done and done.get("file") and Path(done["file"]).exists():
            continue

        path = target_path(rec)
        if path.exists() and path.stat().st_size > 0 and key not in state:
            state[key] = {"status": "ok", "file": str(path), "source": "existing",
                          "quality": rec.get("quality", ""), "size": path.stat().st_size}
            STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                             encoding="utf-8")
            continue
        n = 1
        while path.exists() and path.stat().st_size > 0:
            path = path.with_name("%s (%d)%s" % (path.stem, n, path.suffix))
            n += 1

        result = {"status": "failed", "file": "", "source": "", "quality": ""}
        try:
            got = fresh_url(rec)
            if got:
                path, size = download(got["url"], path)
                result = {"status": "ok", "file": str(path),
                          "source": "netease", "quality": got["level"], "size": size}
            else:
                f = bili_audio(rec, path)
                result = {"status": "ok", "file": str(f), "source": "bilibili",
                          "quality": "30280", "size": f.stat().st_size}
        except Exception as e:
            if result["source"] != "bilibili":
                try:
                    f = bili_audio(rec, path)
                    result = {"status": "ok", "file": str(f), "source": "bilibili",
                              "quality": "30280", "size": f.stat().st_size}
                except Exception as e2:
                    result["error"] = "%s | %s" % (e, e2)
            else:
                result["error"] = str(e)

        state[key] = result
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print("[%3d/%d] %s %s -> %s" % (
            rec["index"] + 1, len(recs), result["status"],
            result.get("source", ""), Path(result["file"]).name if result["file"] else ""),
            flush=True)
        time.sleep(0.4)

    ok = sum(1 for v in state.values() if v.get("status") == "ok")
    print("DONE %d ok / %d" % (ok, len(recs)))


if __name__ == "__main__":
    main()
