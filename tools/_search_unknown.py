import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resolve_all as R

QUERIES = {
    0: ["塞尔达传说 时之笛 主题曲", "時のオカリナ タイトル 近藤浩治"],
    8: ["ウルトラマンダイナ 矢野立美", "戴拿奥特曼 开场曲"],
    13: ["ウルトラマンダイナ 前田達也", "戴拿奥特曼 主题曲"],
    54: ["Kanye West Lord You're Holy Sunday Service"],
    98: ["星と僕らと 目黒将司", "Persona 5 星と僕らと"],
    120: ["il vento d'oro 菅野祐悟", "JOJO 黄金处刑曲"],
    121: ["KiraraMagic 白金之星", "白金之星处刑曲 KiraraMagic"],
    133: ["浆果 TINY 7"],
    134: ["sleepyhead Submarine Boy"],
    136: ["I Love You So The Walters"],
    190: ["What Is Love Haddway"],
    212: ["Mystery of Love Luke Pickman"],
    215: ["Resonance HOME", "Resonance 0.9 HOME"],
    216: ["Memory Reboot VØJ Narvent"],
    226: ["G Sound home"],
    229: ["落日飞行器 XALER"],
    230: ["我好像什么都不缺 又好像什么都没有"],
    243: ["失恋的小鲨鱼"],
    263: ["Lullaby Enzalla"],
    269: ["黑暗森林 雲翼星辰", "我的三体 黑暗森林 主题曲"],
    281: ["活着 郝云"],
    287: ["心墙 郭静"],
    312: ["追光者 岑宁儿"],
    323: ["DOAR CU TINE Activ"],
    325: ["DOAR CU TINE Activ remix 阿鸿"],
    326: ["Blue Jetta HOME"],
    342: ["关山酒 邓寓君", "关山酒 等什么君"],
    346: ["听 张杰 dj"],
    347: ["I Really Want to Stay at Your House Samuel Kim"],
    358: ["Summer 久石譲"],
    368: ["快乐女孩 刘惜君"],
    370: ["Fortunate Son Creedence Clearwater Revival"],
    383: ["Young For You GALA"],
}

out = {}
for k, qs in QUERIES.items():
    print("### key", k)
    hits = []
    for q in qs:
        try:
            for c in R.search(q, 6):
                if c["id"] in {h["id"] for h in hits}:
                    continue
                hits.append(c)
                print("  %s | %s | %s | %ss | %s" % (
                    c["id"], c["name"], c["artist"], c["duration"], c["album"]))
        except Exception as e:
            print("  ERR", e)
        time.sleep(0.35)
    out[str(k)] = hits

Path(r"D:\music\_research\unknown_search.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
