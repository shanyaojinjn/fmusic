# -*- coding: utf-8 -*-
"""Generate 音乐库说明.md (library doc + full categorized track list)."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\music")
DEST = ROOT / "downloads"
OUT = ROOT / "音乐库说明.md"

recs = json.load(open(ROOT / "_research" / "resolve.json", encoding="utf-8"))
state = json.load(open(ROOT / "_research" / "download_state.json", encoding="utf-8"))

CAT_ORDER = ["经典老歌", "华语流行", "欧美", "日语·ACG", "游戏·影视·BGM"]
CAT_DESC = {
    "经典老歌": "2005 年前发行或经典歌手作品，全部按母带（24bit/192kHz FLAC）优先下载。",
    "华语流行": "华语、粤语、民谣、说唱等中文作品。",
    "欧美": "英文及俄语、韩语等非中文流行、电音、摇滚。",
    "日语·ACG": "日语流行与 ACG 相关曲目。",
    "游戏·影视·BGM": "游戏、动画、影视原声与纯音乐。",
}

groups = defaultdict(list)
seen = set()
for k, st in sorted(state.items(), key=lambda kv: int(kv[0])):
    f = st.get("file")
    if not f or f in seen:
        continue
    p = Path(f)
    if not p.exists():
        continue
    seen.add(f)
    r = recs[int(k)]
    m = r.get("match") or {}
    src = st.get("source") or ""
    if src in ("", "existing"):
        src = "bilibili" if st.get("quality") == "30280" else "netease"
    groups[r["category"]].append({
        "no": r["index"] + 1,
        "name": m.get("name") or r["song"],
        "artist": m.get("artist") or r["artist"] or "未知歌手",
        "src": "B站" if src == "bilibili" else "网易云",
        "quality": st.get("quality") or "",
        "ext": p.suffix.lstrip(".").upper(),
        "mb": (st.get("size") or 0) / 1048576 if not p.exists() else p.stat().st_size / 1048576,
        "path": p,
    })

total_files = sum(len(v) for v in groups.values())
total_mb = sum(x["mb"] for v in groups.values() for x in v)
n_master = sum(1 for v in groups.values() for x in v if x["quality"] == "master")
n_flac = sum(1 for v in groups.values() for x in v if x["quality"] == "flac")
n_bili = sum(1 for v in groups.values() for x in v if x["quality"] == "30280")
n_lrc = sum(1 for v in groups.values() for x in v
            if x["path"].with_suffix(".lrc").exists())

md = []
md.append("# 本地音乐库说明\n")
md.append("> 由 B 站收藏夹自动解析、匹配并下载生成。收藏夹地址：\n"
          "> https://space.bilibili.com/284606217/favlist?fid=2918085717&ftype=create\n")
md.append("## 一、总览\n")
md.append("| 项目 | 数值 |\n| --- | --- |")
md.append("| 收藏条目 | 389 首 |")
md.append("| 去重后文件 | %d 个 |" % total_files)
md.append("| 总体积 | %.2f GB |" % (total_mb / 1024))
md.append("| 网易云母带 FLAC | %d 首 |" % n_master)
md.append("| 网易云普通 FLAC | %d 首 |" % n_flac)
md.append("| B 站音轨兜底 | %d 首 |" % n_bili)
md.append("| 内嵌封面 | %d 首（全部） |" % total_files)
md.append("| 内嵌 + 外挂歌词 | %d 首 |" % n_lrc)
md.append("")
md.append("分类统计：\n")
md.append("| 分类 | 曲目数 | 说明 |\n| --- | --- | --- |")
for c in CAT_ORDER:
    md.append("| %s | %d | %s |" % (c, len(groups[c]), CAT_DESC[c]))
md.append("")
md.append("## 二、目录结构\n")
md.append("```text")
md.append(r"D:\music")
md.append(r"├─ downloads\                  音乐库（按分类分文件夹）")
md.append(r"│  ├─ _manifest.csv            总清单（Excel 可打开，UTF-8 BOM）")
md.append(r"│  ├─ 播放列表\                 每个分类一个 .m3u8 播放列表")
md.append(r"│  ├─ *.lrc                    与音频同名的歌词文件（可直接被播放器读取）")
md.append(r"│  ├─ 经典老歌\ 华语流行\ 欧美\ 日语·ACG\ 游戏·影视·BGM\ ")
md.append(r"├─ tools\                      解析 / 下载 / 清单脚本")
md.append(r"│  ├─ resolve_all.py           匹配歌曲并解析下载链接")
md.append(r"│  ├─ download_all.py          按 resolve.json 下载，失败自动切 B 站")
md.append(r"│  ├─ make_manifest.py         生成 _manifest.csv")
md.append(r"│  ├─ make_playlists.py        生成分类 m3u8")
md.append(r"│  ├─ tag_library.py           刮削并写入封面 / 歌词 / 歌手 / 专辑标签")
md.append(r"├─ _research\                  解析结果与运行日志")
md.append(r"│  ├─ favorites.json           收藏夹原始数据（389 条）")
md.append(r"│  ├─ resolve.json             每首歌的匹配结果、来源、音质、封面等")
md.append(r"│  ├─ download_state.json      每个索引对应的文件路径与状态")
md.append(r"├─ bbdown\                     yt-dlp / ffmpeg / 登录 cookies")
md.append(r"└─ lx-music\                   LX Music 绿色版（13 个第三方音源）")
md.append("```")
md.append("")
md.append("## 三、音质策略\n")
md.append("- **经典老歌**：优先请求 `master`（母带，实际为 24bit/192kHz FLAC），"
          "不可用时依次降级 `flac` → `320k`。")
md.append("- **其他分类**：优先 `flac`（多为 16bit/44.1kHz 无损）→ `320k` MP3。")
md.append("- **平台搜不到**（%d 首）：改用 B 站原视频音轨，"
          "由 yt-dlp 拉取最高音频流（format 30280，约 232k AAC）。" % n_bili)
md.append("- 下载时会校验文件头与大小，小于 100KB 视为失败并自动重试兜底源。")
md.append("")
md.append("## 四、清单文件 `_manifest.csv`\n")
md.append("字段：序号、分类、歌名、歌手、专辑、来源、音质、格式、大小MB、时长、"
          "文件名、B站原视频、状态、备注。\n"
          "核对错配时，用「B站原视频」列点回原视频比对最快。\n")
md.append("## 五、播放列表\n")
md.append("`downloads\\播放列表\\` 下按分类生成 `.m3u8`（UTF-8、相对路径），"
          "可直接拖入 foobar2000 / AIMP / PotPlayer / VLC 播放，"
          "也可用 MusicBee、Navidrome 等媒体库软件导入。\n")
md.append("## 六、封面 / 歌词 / 标签\n")
md.append("已对全部 %d 个文件写入内嵌元数据：\n" % total_files)
md.append("- **封面**：网易云专辑封面（600×600，内嵌到 FLAC/MP3/M4A）；"
          "B 站兜底曲目使用原视频封面。")
md.append("- **歌词**：共 %d 首带 LRC 歌词，既内嵌到音频标签，也在同目录生成同名 `.lrc`；"
          "纯音乐、B 站合集与部分冷门曲目无歌词。" % n_lrc)
md.append("- **歌手 / 专辑 / 年份**：来自网易云曲库；B 站兜底曲目填实际歌手，"
          "专辑统一记为「B站收藏」。")
md.append("- **注释字段**：记录来源与 B 站原视频链接，便于回溯核对。")
md.append("- 重新刮削：`python tools/tag_library.py`（带缓存，增量很快）。\n")
md.append("## 七、下载方法（流程）\n")
md.append("1. **取收藏夹**：调用 B 站收藏夹接口，保存 389 条记录"
          "（标题、时长、bvid、分P）到 `_research/favorites.json`。")
md.append("2. **解析标题**：去掉「百万级录音棚」「Hi-Res」「日推歌单」等噪音词，"
          "用《》、`A - B`、拉丁文片段等规则提取「歌名 + 歌手」。")
md.append("3. **平台搜索**：调用网易云 `cloudsearch/pc` 接口，"
          "用「歌名 歌手」多组关键词检索候选。")
md.append("4. **匹配打分**：歌名相似度 0.60 + 歌手相似度 0.25 + 时长相似度 0.15，"
          "并惩罚翻唱/排名靠后的结果；阈值：歌名 ≥0.85，歌手 ≥0.55。")
md.append("5. **解析音质**：向第三方解析接口 `POST https://c.wwwweb.top/music/url` "
          "提交 `{\"source\":\"wy\",\"musicId\":\"<id>\",\"quality\":\"master|flac|320k\"}`，"
          "返回真实音频直链。")
md.append("6. **下载落盘**：按 `分类/歌手 - 歌名.flac` 命名，"
          "先写 `.part` 再按文件头嗅探真实格式（FLAC/MP3/M4A）后改名。")
md.append("7. **B 站兜底**：平台无结果或解析失败时，"
          "用 `bbdown\\yt-dlp.exe` + 登录 cookies 拉取 `bestaudio[format_id=30280]`。")
md.append("8. **断点续跑**：`resolve.json` 以 bvid 去重，"
          "`download_state.json` 以序号记录文件，重跑自动跳过已完成项。")
md.append("")
md.append("## 八、常用命令\n")
md.append("```bash")
md.append("cd /d/music")
md.append("# 1) 重新匹配（会跳过已解析的 bvid；改完解析规则可先删 resolve.json）")
md.append("PYTHONIOENCODING=utf-8 python tools/resolve_all.py")
md.append("# 2) 下载 / 续传（已存在文件自动跳过）")
md.append("PYTHONIOENCODING=utf-8 python tools/download_all.py")
md.append("# 3) 重建清单与播放列表")
md.append("PYTHONIOENCODING=utf-8 python tools/make_manifest.py")
md.append("PYTHONIOENCODING=utf-8 python tools/make_playlists.py")
md.append("```")
md.append("")
md.append("依赖：Python 3（仅标准库）、`bbdown/yt-dlp.exe`、`bbdown/ffmpeg.exe`、"
          "`bbdown/cookies.txt`（B 站登录态）。cookies 过期后重新扫码登录即可。\n")
md.append("## 九、LX Music（落雪）\n")
md.append("绿色版位于 `D:\\music\\lx-music`，已内置 13 个第三方音源"
          "（长青、fish、野花、野草、helloworld、幻音、HYW、杰翔、聚合、全豆要、六音、星海、玉宁熙），"
          "默认音源为 `lx-玉宁熙-Pro`。\n"
          "> 已排除 huibq（禁止批量下载）与 ikun（接口域名失效）。\n"
          "> 第三方音源来自公开社区，稳定性随时可能变化；本库已把文件下载到本地，不依赖它们在播放时联网。\n")
md.append("## 十、已知限制\n")
md.append("- %d 个文件（对应 %d 条收藏）在网易云无匹配，只能用 B 站音轨（约 128–232k AAC），"
          "是 B 站侧能拿到的最高音质。" % (n_bili, sum(1 for v in recs if v["status"] == "bili")))
md.append("- 歌词覆盖 %d/%d：纯音乐与 B 站合集本身没有歌词，属于正常情况。" % (n_lrc, total_files))
md.append("- 极少数同名翻唱、纯音乐改编可能匹配到非原唱；"
          "用 `_manifest.csv` 的 B 站链接核对，按序号可单独换源。")
md.append("- 同一首歌被收藏两次时只保留一个文件，清单中两行会指向同一文件。")
md.append("- 本库仅供个人离线收听，请勿再分发。")
md.append("")
md.append("## 十一、完整歌单\n")
for c in CAT_ORDER:
    items = sorted(groups[c], key=lambda x: x["name"].lower())
    md.append("### %s（%d 首）\n" % (c, len(items)))
    md.append("| # | 歌名 | 歌手 | 来源 | 格式 | 大小 |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for x in items:
        q = "母带FLAC" if x["quality"] == "master" else (
            "FLAC" if x["ext"] == "FLAC" else "%s %s" % (
                x["ext"], x["quality"] if x["quality"] != "30280" else "AAC"))
        name = x["name"].replace("|", "｜")
        artist = x["artist"].replace("|", "｜")
        md.append("| %d | %s | %s | %s | %s | %.1f MB |" % (
            x["no"], name, artist, x["src"], q, x["mb"]))
    md.append("")

OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", OUT, len(md), "lines")
