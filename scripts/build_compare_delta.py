#!/usr/bin/env python3
"""
改定前は後発<先発だったのに、改定後に後発≧先発になった品目を抽出する。
"""

import json
import sys
from pathlib import Path
def pairwise(iterable):
    it = iter(iterable)
    a = next(it, None)
    for b in it:
        yield a, b
        a = b


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_delta(old_data, new_data):
    key = lambda r: (r["seibun"], r["kikaku"], r["senpatu_hinmei"])
    old_map = {key(r): r for r in old_data["rows"]}
    new_map = {key(r): r for r in new_data["rows"]}

    results = []
    for k, nr in new_map.items():
        or_ = old_map.get(k)
        if not or_:
            continue
        if or_["diff"] > 0 and nr["diff"] <= 0:
            results.append({
                "kubun":           nr["kubun"],
                "seibun":          nr["seibun"],
                "kikaku":          nr["kikaku"],
                "senpatu_hinmei":  nr["senpatu_hinmei"],
                "senpatu_maker":   nr["senpatu_maker"],
                "senpatu_type":    nr["senpatu_type"],
                "old_senpatu":     or_["senpatu_yakka"],
                "new_senpatu":     nr["senpatu_yakka"],
                "old_kouhatsu_min": or_["kouhatsu_min"],
                "new_kouhatsu_min": nr["kouhatsu_min"],
                "old_diff":        or_["diff"],
                "new_diff":        nr["diff"],
                "kouhatsu_list":   nr["kouhatsu_list"],
            })

    results.sort(key=lambda r: r["old_diff"], reverse=True)
    return results


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/data")

    cmp_files = sorted(data_dir.glob("compare_*.json"))
    for old_path, new_path in pairwise(cmp_files):
        old = load(old_path)
        new = load(new_path)
        rows = build_delta(old, new)
        out = data_dir / f"compare_delta_{old['version']}_{new['version']}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump({
                "from": old["version"], "to": new["version"], "rows": rows
            }, f, ensure_ascii=False, separators=(",", ":"))
        print(f"✓ {old['version']} → {new['version']}: {len(rows)} 件 → {out.name}")
