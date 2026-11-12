import re
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent / "pdone"
RE_HOST = re.compile(r"https?://((?:[A-Za-z0-9-]+\.)+(?:xn--[A-Za-z0-9-]+|[A-Za-z]{2,}))")
RE_IPV4 = re.compile(r"https?://((?:\d{1,3}\.){3}\d{1,3})")
RE_HEX_RUN = re.compile(r"(?:\\x[0-9a-fA-F]{2}){4,}")
RE_HEX_BYTE = re.compile(r"\\x([0-9a-fA-F]{2})")
RE_SERVER_CONFIG = re.compile(r"SERVER_SCRIPT_CONFIG'?\]?\s*=\s*(\{[^{}]*\})")
BLOCK = {"www.w3.org", "gistry.npm"}


def hosts_of(text):
    hosts = set()
    for rx in (RE_HOST, RE_IPV4):
        hosts.update(m.lower() for m in rx.findall(text))
    for run in RE_HEX_RUN.findall(text):
        try:
            dec = bytes(int(h, 16) for h in RE_HEX_BYTE.findall(run)).decode("ascii")
        except (ValueError, UnicodeDecodeError):
            continue
        for rx in (RE_HOST, RE_IPV4):
            hosts.update(m.lower() for m in rx.findall(dec))
    for raw in RE_SERVER_CONFIG.findall(text):
        try:
            cfg = json.loads(raw)
        except ValueError:
            continue
        u = cfg.get("apiUrl") or cfg.get("api_url")
        if u:
            h = urlsplit(u).hostname
            if h:
                hosts.add(h.lower())
    return hosts - BLOCK


def probe(host):
    scheme = "http" if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", host) else "https"
    url = f"{scheme}://{host}/"
    try:
        req = Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=8) as r:
            return host, f"OK {r.status}"
    except HTTPError as e:
        return host, f"HTTP {e.code}"
    except Exception as e:
        return host, f"FAIL {type(e).__name__}"


def main():
    sources = []
    for latest in sorted(ROOT.glob("*/latest.js")):
        sources.append((latest.parent.name, sorted(hosts_of(latest.read_text(encoding="utf-8", errors="ignore")))))
    hosts = sorted({h for _, hs in sources for h in hs})
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = dict(pool.map(probe, hosts))
    for name, hs in sources:
        print(f"[{name}]")
        for h in hs:
            print(f"   {h:42s} {results[h]}")


if __name__ == "__main__":
    main()
