#!/usr/bin/env python3
"""Remove confirmed-dead tools from index.html (the source). Prints JSON: {"removed": [...], "skipped": "..."}.

Uses check_links.check(), so the same rules apply: 3 tries before condemning, parked
domains count as dead, timeouts and runner network errors do NOT. If more than MAX_SHARE
of the list comes back dead at once, that is the network, not the web — nothing is removed.
Run build_site.py afterwards so tools.json / README follow.
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from add_tools import find_array  # noqa: E402
from check_links import check  # noqa: E402

INDEX = os.path.join(ROOT, "index.html")
MAX_SHARE = 0.05


def main():
    html = open(INDEX, encoding="utf-8").read()
    s, e = find_array(html)
    toys = json.loads(html[s:e])
    with ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(check, toys))
    dead = {r["url"]: r for r in results if not r["alive"]}
    if len(dead) > max(3, MAX_SHARE * len(toys)):
        print(json.dumps({"removed": [], "skipped": f"{len(dead)} of {len(toys)} dead at once — looks like the network, removed nothing"}))
        return 0
    keep = [t for t in toys if t["u"] not in dead]
    if len(keep) != len(toys):
        html = html[:s] + json.dumps(keep, ensure_ascii=False) + html[e:]
        open(INDEX, "w", encoding="utf-8").write(html)
    print(json.dumps({"removed": [{"n": r["name"], "u": r["url"], "why": str(r["code"] or r["err"])} for r in dead.values()], "checked": len(toys)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
