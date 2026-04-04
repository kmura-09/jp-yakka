#!/usr/bin/env python3
"""
改定前後で先発・後発の価格逆転が起きた品目を抽出する。
- flipped:  前回は後発<先発 → 今回は後発≧先発（後発が追いついた）
- restored: 前回は後発≧先発 → 今回は後発<先発（先発が下がって差が戻った）
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


def make_entry(or_, nr):
    return {
        "kubun":            nr["kubun"],
        "seibun":           nr["seibun"],
        "kikaku":           nr["kikaku"],
        "senpatu_hinmei":   nr["senpatu_hinmei"],
        "senpatu_maker":    nr["senpatu_maker"],
        "senpatu_type":     nr["senpatu_type"],
        "old_senpatu":      or_["senpatu_yakka"],
        "new_senpatu":      nr["senpatu_yakka"],
        "old_kouhatsu_min": or_["kouhatsu_min"],
        "new_kouhatsu_min": nr["kouhatsu_min"],
        "old_diff":         or_["diff"],
        "new_diff":         nr["diff"],
        "kouhatsu_list":    nr["kouhatsu_list"],
    }


def build_delta(old_data, new_data):
    key = lambda r: (r["seibun"], r["kikaku"], r["senpatu_hinmei"])
    old_map = {key(r): r for r in old_data["rows"]}
    new_map = {key(r): r for r in new_data["rows"]}

    flipped  = []  # 前回は後発<先発 → 今回は後発≧先発
    restored = []  # 前回は後発≧先発 → 今回は後発<先発

    for k, nr in new_map.items():
        or_ = old_map.get(k)
        if not or_:
            continue
        if or_["diff"] > 0 and nr["diff"] <= 0:
            flipped.append(make_entry(or_, nr))
        elif or_["diff"] <= 0 and nr["diff"] > 0:
            restored.append(make_entry(or_, nr))

    flipped.sort(key=lambda r: r["old_diff"], reverse=True)
    restored.sort(key=lambda r: r["new_diff"], reverse=True)
    return flipped, restored


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/data")

    cmp_files = sorted(data_dir.glob("compare_[0-9]*.json"))
    for old_path, new_path in pairwise(cmp_files):
        old = load(old_path)
        new = load(new_path)
        flipped, restored = build_delta(old, new)
        out = data_dir / f"compare_delta_{old['version']}_{new['version']}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump({
                "from": old["version"], "to": new["version"],
                "flipped": flipped, "restored": restored,
            }, f, ensure_ascii=False, separators=(",", ":"))
        print(f"✓ {old['version']} → {new['version']}")
        print(f"  後発≧先発になった: {len(flipped)} 件")
        print(f"  後発<先発に戻った: {len(restored)} 件  → {out.name}")
