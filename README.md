# 本地音乐库 fmusic

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Tracks](https://img.shields.io/badge/tracks-390-1db954)
![Audio](https://img.shields.io/badge/audio-14.8%20GB-1db954)
![License](https://img.shields.io/badge/license-MIT-blue)
![Audio](https://img.shields.io/badge/audio-not%20in%20repo-lightgrey)

从 B 站收藏夹整理出来的本地音乐库：**390 条记录、362 个唯一音频文件、约 14.8 GB**。
优先从网易云第三方解析拿 FLAC / 母带，平台没有的歌用 B 站原视频音频兜底；
每条都已写入封面、歌词（`.lrc` 同名文件）、歌手、专辑、年份标签。

> 音频文件本身不进 Git（见文末「版本管理」）；这份 README 和清单是给人和 AI 的操作手册。

```bash
git clone https://github.com/shanyaojinjn/fmusic.git
cd fmusic
pip install -r requirements.txt
```

## 目录

- [快速开始](#一快速开始)
- [搜索音乐](#二搜索音乐)
- [目录结构](#三目录结构)
- [清单字段](#四清单字段)
- [音质策略](#五音质策略)
- [往库里加一首歌](#六往库里加一首歌)
- [脚本一览](#七脚本一览tools)
- [版本管理](#八版本管理git)
- [已知限制](#九已知限制)
- [许可](#十许可)

---

## 一、快速开始

| 想做什么 | 怎么做 |
|---|---|
| 按分类随便听 | 打开 `downloads/` 下的分类文件夹，双击任意音频 |
| 整类播放 | 把 `downloads/播放列表/*.m3u8` 拖进 foobar2000 / AIMP / PotPlayer / VLC |
| 导入媒体库 | 在播放器里把 `D:\music\downloads` 加为音乐文件夹，让它自己扫描标签 |
| 查某首歌有没有 | 用第二节的任意一种搜索方式 |

播放列表文件（UTF-8、相对路径）：
`华语流行.m3u8`、`欧美.m3u8`、`经典老歌.m3u8`、`游戏·影视·BGM.m3u8`、`日语·ACG.m3u8`。

---

## 二、搜索音乐

### 1. 命令行（推荐）

```bash
python tools/search.py 雨爱
python tools/search.py --artist 杨丞琳
python tools/search.py --category 欧美 --quality flac
python tools/search.py 雨爱 --json      # JSON 输出，方便脚本 / AI 读取
```

- 多个关键字是 **AND** 关系，匹配歌名、歌手、专辑、文件名、分类；
- 输出每行：`序号  歌名  歌手  专辑  音质  大小  绝对路径`；
- `--limit N` 控制条数（默认 50）。

### 2. 直接查清单

用 Excel / WPS 打开 `downloads/_manifest.csv`（UTF-8 BOM，可直接双击），
按「歌名 / 歌手 / 分类」筛选。字段含义见第四节。

### 3. 纯文本搜索

```bash
grep -i 雨爱 downloads/_manifest.csv
```

### 4. 给 AI / 脚本的检索约定

1. **唯一索引**是 `downloads/_manifest.csv`，不要扫描音频文件来猜；
2. **路径**永远是 `downloads/<分类>/<文件名>`，`文件名` 列已包含 `歌手 - 歌名`，
   重名时带 ` (1)`、` (2)` 后缀——不要自己拼文件名；
3. 多个「序号」可能指向**同一个文件**（同一首歌在收藏夹里出现多次），去重后
   实际只有 362 个文件；
4. `音质` 列取值：`master`（母带）、`flac`（无损）、`320k`（有损 MP3）、
   `30280`（B 站 AAC，约 232 kbps）；
5. 「B站原视频」列可直接点开原视频核对错配；手动追加的曲目写「（手动追加）」；
6. 程序化检索建议 `python tools/search.py --json`，返回绝对路径和全部字段。

---

## 三、目录结构

```
D:\music
├─ downloads\                 # 音乐库本体
│  ├─ 华语流行\               # 81 首
│  ├─ 欧美\                   # 187 首
│  ├─ 经典老歌\               # 52 首
│  ├─ 游戏·影视·BGM\          # 34 首
│  ├─ 日语·ACG\               # 8 首
│  ├─ 播放列表\               # 每个分类一个 .m3u8
│  └─ _manifest.csv           # 全库清单（唯一索引）
├─ tools\                     # 下载 / 解析 / 打标签 / 生成清单的脚本
├─ _research\                 # 抓取与匹配的中间数据（resolve.json 等）
├─ bbdown\                    # yt-dlp + ffmpeg + B 站 cookies（B 站兜底用）
├─ lx-music\                  # LX Music 便携版（第三方音源）
├─ 音乐库说明.md              # 建库过程、完整歌单、技术细节
└─ README.md                  # 本文件
```

更详细的建库过程、完整歌单和参数说明见 [音乐库说明.md](音乐库说明.md)。

---

## 四、清单字段

| 字段 | 说明 |
|---|---|
| 序号 | 对应收藏夹顺序（1 起）；新增歌曲顺延 |
| 分类 | 华语流行 / 欧美 / 经典老歌 / 游戏·影视·BGM / 日语·ACG |
| 歌名、歌手、专辑 | 来自平台匹配结果，已写入音频标签 |
| 来源 | 网易云 / B站 |
| 音质 | master / flac / 320k / 30280（B 站） |
| 格式 | FLAC / MP3 / M4A |
| 大小MB、时长 | 文件大小与歌曲时长 |
| 文件名 | 磁盘上的真实文件名（不含分类目录） |
| B站原视频 | 原始视频链接，核对错配用 |
| 状态 | ok / failed |
| 备注 | 失败原因或特殊说明 |

---

## 五、音质策略

1. **经典老歌**优先 `master`（母带），其次 `flac`、`320k`；
2. 其他歌曲优先 `flac`，其次 `320k`；
3. 平台搜不到、解析失败或只有低码率时，回退 B 站音频（AAC 约 232 kbps），
   清单里音质记为 `30280`；
4. 下载后按文件头嗅探真实格式再改扩展名，避免「假 FLAC」。

当前分布（按记录）：网易云 347 条（57 母带 + 290 FLAC）、B 站 43 条。

---

## 六、往库里加一首歌

以「雨爱 DJ 版」为例，完整流程：

```bash
# 1. 搜候选（网易云 cloudsearch）
python - <<'PY'
import sys; sys.path.insert(0, 'tools')
import resolve_all as R
for c in R.search('雨爱 DJ版', 10):
    print(c['id'], c['name'], c['artist'], c['duration'], 's')
PY

# 2. 测试能否解析到直链（flac → 320k 自动回退）
python - <<'PY'
import sys; sys.path.insert(0, 'tools')
import resolve_all as R
print(R.resolve_url(3375731947, 'flac'))
PY
```

3. 在 `_research/resolve.json` 末尾追加一条记录（`index` 顺延），
   把 `match` 填成平台搜索结果、`quality` 填目标音质；
4. 运行 `python tools/download_all.py`（可断点续传，只下没下过的）；
5. 给新文件打标签：`tag_library.main()` 按 `download_state.json` 遍历，
   或只处理新增序号；
6. 重建清单、播放列表和说明文档：

```bash
python tools/make_manifest.py
python tools/make_playlists.py
python tools/make_doc.py
```

---

## 七、脚本一览（`tools/`）

| 脚本 | 作用 |
|---|---|
| `resolve_all.py` | 解析标题、搜索网易云、打分匹配、取音频直链 |
| `download_all.py` | 批量下载（网易云优先、B 站兜底），断点续传 |
| `tag_library.py` | 刮削并写入封面、歌词、歌手、专辑、年份 |
| `make_manifest.py` | 生成 `downloads/_manifest.csv` |
| `make_playlists.py` | 生成分类 `.m3u8` |
| `make_doc.py` | 生成 `音乐库说明.md` |
| `search.py` | **检索本地库**（本 README 第二节） |
| `fix_*.py`、`apply_unknown_fix.py` | 历史修正脚本（匹配纠错、佚名歌手补全） |

---

## 八、版本管理（Git）

**上传**：脚本、`_research` 中的 JSON 与音源 JS、`_manifest.csv`、
播放列表、两份 Markdown（本 README 与 `音乐库说明.md`）。

**不上传**（已在 `.gitignore` 中排除）：

- `downloads/` 下的音频（`.flac` `.mp3` `.m4a` `.ogg` `.wav` 等）与 `.lrc` 歌词；
- `_research/tag_cache/`（封面/歌词抓取缓存）；
- `bbdown/`、`lx-music/` 的程序与二进制（体积大，可重新下载）；
- `__pycache__`、运行日志。

因此 clone 仓库后**只有索引和脚本**，音乐需要按本文流程重新下载，
或把 `downloads` 目录单独拷过来。

---

## 九、已知限制

- 第三方解析接口（`c.wwwweb.top`）可能随时失效，失效时只能走 B 站兜底；
- 43 首 B 站兜底曲目是 AAC 有损，不是无损；
- 极少数冷门曲目平台没有，只能保留 B 站版本；
- 仅供个人离线收听，请勿传播或用于商业用途。

---

## 十、许可

仓库中的脚本与文档以 [MIT License](LICENSE) 发布。
音频文件不在仓库内，其版权归原作者及发行方所有。

