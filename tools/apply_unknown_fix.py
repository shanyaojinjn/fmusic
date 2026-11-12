# -*- coding: utf-8 -*-
"""Identify/rename files that had '未知歌手', replacing with real tracks."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R
import download_all as D

ROOT = Path(r"D:\music")
RES = ROOT / "_research" / "resolve.json"
STATE = ROOT / "_research" / "download_state.json"

# key -> (netease_id, song, artist, category or None)
REPLACE = {
    0: (22761262, "塞尔达传说 时之笛 主题曲", "近藤浩治", "游戏·影视·BGM"),
    13: (28606207, "ウルトラマンダイナ", "前田達也", "游戏·影视·BGM"),
    98: (864433794, "星と僕らと", "Lyn", "日语·ACG"),
    120: (1334780738, "il vento d'oro", "菅野祐悟", "游戏·影视·BGM"),
    121: (1347846723, "JOJO的奇妙冒险白金之星处刑曲电音版", "Kirara Magic", "游戏·影视·BGM"),
    133: (2015896805, "浆果", "TINY7", None),
    134: (1320884184, "sleepyhead", "submarine boy", None),
    136: (1294899297, "I Love You So", "The Walters", None),
    190: (26970162, "What Is Love", "Haddaway", None),
    212: (1457681678, "Mystery of Love", "Luke Pickman", None),
    215: (1322030323, "Resonance", "HOME", None),
    216: (2074219270, "Memory Reboot (Slowed)", "VØJ/Narvent", None),
    226: (2108770099, "Home", "G Sounds", None),
    229: (1467115424, "落日飞行器", "XALER", None),
    230: (2149622625, "我好像什么都不缺", "monster", None),
    243: (1982975742, "真夜中のドア〜stay with me", "松原みき", "经典老歌"),
    263: (1939751157, "Lullaby", "Enzalla", None),
    264: (1992762997, "不怕 (CD版)", "赵蓓/赵蕾", None),
    269: (416892104, "黑暗森林", "雲翼星辰", None),
    281: (27646786, "活着", "郝云", None),
    287: (27671269, "心墙", "郭静", None),
    312: (483671599, "追光者", "岑宁儿", None),
    323: (16442343, "Doar Cu Tine", "Activ", None),
    326: (1820673129, "home", "BleuJetta", None),
    347: (1990743306, "I Really Want to Stay at Your House", "Samuel Kim/Lorien", None),
    358: (442986, "Summer", "久石譲", "经典老歌"),
    368: (255184, "快乐女孩", "刘惜君", None),
    370: (20545072, "Fortunate Son", "Creedence Clearwater Revival", None),
}

# key -> (song, artist, category)  keep Bilibili audio, just label it
KEEP = {
    8: ("戴拿奥特曼 开场音乐", "矢野立美", "游戏·影视·BGM"),
    11: ("三杰的至暗时刻", "群星", "游戏·影视·BGM"),
    14: ("奥特曼三杰片头曲", "群星", "游戏·影视·BGM"),
    54: ("Lord You're Holy (Sunday Service)", "Kanye West", "欧美"),
    65: ("合成器浪潮五首合集", "群星", "欧美"),
    188: ("生化危机4 重制版 画质对比", "Capcom", "游戏·影视·BGM"),
    191: ("欧美循环歌单", "群星", "欧美"),
    192: ("英文老歌100精选", "群星", "欧美"),
    194: ("接着奏乐接着舞", "群星", "欧美"),
    208: ("车载嗨曲合集", "群星", "欧美"),
    265: ("老歌DJ合集", "群星", "华语流行"),
    321: ("宿命感BGM合集", "群星", "游戏·影视·BGM"),
    325: ("Doar Cu Tine (阿鸿 Remix)", "阿鸿", "欧美"),
    329: ("硬曲降调", "群星", "欧美"),
    342: ("关山酒 (降调版)", "邓寓君", "华语流行"),
    346: ("听 (DJ版)", "张杰", "华语流行"),
    383: ("Young For You", "GALA", "欧美"),
}


def detail(song_id):
    d = R.http_json("https://music.163.com/api/song/detail?ids=[%d]" % song_id)
    s = (d.get("songs") or [None])[0]
    if not s:
        return None
    al = s.get("album") or {}
    return {
        "id": s.get("id"),
        "name": s.get("name") or "",
        "alia": [],
        "artist": "/".join(a.get("name", "") for a in (s.get("artists") or [])),
        "album": al.get("name") or "",
        "cover": al.get("picUrl") or "",
        "duration": (s.get("duration") or 0) // 1000,
        "fee": s.get("fee"),
        "year": 0,
    }


def main():
    recs = json.load(open(RES, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))

    for key, (sid, song, artist, cat) in REPLACE.items():
        rec = recs[key]
        c = detail(sid)
        if not c:
            print(key + 1, "detail failed", sid)
            continue
        levels = ["master", "flac", "320k"] if (cat == "经典老歌" or rec["category"] == "经典老歌") else ["flac", "320k"]
        hit = None
        for q in levels:
            hit = R.resolve_url(sid, q)
            if hit:
                break
        if not hit:
            print(key + 1, "no url", sid, c["name"])
            continue
        old = state.get(str(key), {})
        if old.get("file") and Path(old["file"]).exists():
            Path(old["file"]).unlink()
        state.pop(str(key), None)
        rec.update({
            "song": song,
            "artist": artist,
            "match": c,
            "status": "ok",
            "quality": hit["level"],
            "url": hit["url"],
            "size": R.head_size(hit["url"]),
            "category": cat or rec["category"],
            "confidence": 0.95,
            "name_sim": 1.0,
            "artist_sim": 1.0,
            "dur_sim": 1.0,
        })
        print(key + 1, "->", c["name"], "|", c["artist"], "|", hit["level"])

    for key, (song, artist, cat) in KEEP.items():
        rec = recs[key]
        rec.update({"song": song, "artist": artist, "category": cat,
                    "match": None, "status": "bili", "quality": "30280"})
        st = state.get(str(key))
        if not st or not st.get("file"):
            print(key + 1, "no file")
            continue
        cur = Path(st["file"])
        if not cur.exists():
            print(key + 1, "missing", cur)
            continue
        want = D.target_path(rec).with_suffix(cur.suffix)
        if want != cur:
            if want.exists():
                cur.unlink()
                print(key + 1, "dedup", cur.name)
            else:
                cur.rename(want)
                print(key + 1, "rename", cur.name, "->", want.name)
            st["file"] = str(want)

    json.dump(recs, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
