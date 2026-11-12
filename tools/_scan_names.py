import json
import re
from pathlib import Path

recs = json.load(open(r"D:\music\_research\resolve.json", encoding="utf-8"))
sk = json.load(open(r"D:\music\_research\download_state.json", encoding="utf-8"))
for k, v in sk.items():
    if not v.get("file"):
        continue
    name = Path(v["file"]).name
    base = Path(v["file"]).stem
    if len(base) > 55 or re.search(r"[！!？?]", base):
        print(k, "|", name)
