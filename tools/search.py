# -*- coding: utf-8 -*-
"""Search the local library index (downloads/_manifest.csv).

Examples:
    python tools/search.py 雨爱
    python tools/search.py --artist 杨丞琳
    python tools/search.py --category 欧美 --quality flac
    python tools/search.py 雨爱 --json
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "downloads" / "_manifest.csv"


def load_rows():
    with open(MANIFEST, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_item(r):
    return {
        "index": r["序号"],
        "category": r["分类"],
        "song": r["歌名"],
        "artist": r["歌手"],
        "album": r["专辑"],
        "source": r["来源"],
        "quality": r["音质"],
        "format": r["格式"],
        "size_mb": r["大小MB"],
        "duration": r["时长"],
        "file": r["文件名"],
        "path": str(ROOT / "downloads" / r["分类"] / r["文件名"]),
    }


def main():
    ap = argparse.ArgumentParser(description="搜索本地音乐库")
    ap.add_argument("keyword", nargs="*", help="关键字，多个词为 AND，匹配歌名/歌手/专辑/文件名")
    ap.add_argument("--artist", help="只匹配该歌手（子串）")
    ap.add_argument("--category", help="只匹配该分类（子串）")
    ap.add_argument("--quality", help="只匹配该音质标记，如 flac / master / 320k / 30280")
    ap.add_argument("--json", action="store_true", help="输出 JSON，便于程序/AI 读取")
    ap.add_argument("--limit", type=int, default=50, help="最多返回条数，默认 50")
    a = ap.parse_args()

    keys = [k.lower() for k in a.keyword]
    hits = []
    for r in load_rows():
        blob = " ".join((r["歌名"], r["歌手"], r["专辑"], r["文件名"], r["分类"])).lower()
        if keys and not all(k in blob for k in keys):
            continue
        if a.artist and a.artist.lower() not in r["歌手"].lower():
            continue
        if a.category and a.category not in r["分类"]:
            continue
        if a.quality and a.quality.lower() not in r["音质"].lower():
            continue
        hits.append(to_item(r))

    hits = hits[: a.limit]
    if a.json:
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return
    if not hits:
        print("没有找到匹配的歌曲")
        return
    for x in hits:
        print("%s\t%s\t%s\t%s\t%s\t%sMB\t%s" % (
            x["index"], x["song"], x["artist"], x["album"],
            x["quality"], x["size_mb"], x["path"]))
    print("共 %d 条" % len(hits))


if __name__ == "__main__":
    main()
