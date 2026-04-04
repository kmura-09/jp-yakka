#!/usr/bin/env python3
"""2つの薬価JSONを比較して差分JSONを生成する"""

import json
import sys
from pathlib import Path


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def diff(old, new):
    old_map = {r["code"]: r for r in old["records"]}
    new_map = {r["code"]: r for r in new["records"]}

    added   = []  # 新規収載
    removed = []  # 削除
    changed = []  # 変更（薬価・同額フラグ等）

    for code, nr in new_map.items():
        if code not in old_map:
            added.append(nr)
        else:
            or_ = old_map[code]
            changes = {}
            if nr["yakka"] != or_["yakka"]:
                changes["yakka"] = {"old": or_["yakka"], "new": nr["yakka"]}
            if nr["dougaku"] != or_["dougaku"]:
                changes["dougaku"] = {"old": or_["dougaku"], "new": nr["dougaku"]}
            if nr["senpatu"] != or_["senpatu"]:
                changes["senpatu"] = {"old": or_["senpatu"], "new": nr["senpatu"]}
            if nr["kouhatsu"] != or_["kouhatsu"]:
                changes["kouhatsu"] = {"old": or_["kouhatsu"], "new": nr["kouhatsu"]}
            if changes:
                changed.append({**nr, "changes": changes})

    for code, or_ in old_map.items():
        if code not in new_map:
            removed.append(or_)

    return {
        "from": old["version"],
        "to":   new["version"],
        "added":   added,
        "removed": removed,
        "changed": changed,
    }


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/data")

    jsons = sorted(data_dir.glob("yakka_*.json"))
    if len(jsons) < 2:
        print("比較するJSONが2つ以上必要です")
        sys.exit(1)

    # 隣接するバージョン間の差分をすべて生成
    for old_path, new_path in zip(jsons, jsons[1:]):
        old = load(old_path)
        new = load(new_path)
        result = diff(old, new)
        out = data_dir / f"diff_{result['from']}_{result['to']}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
        print(f"✓ diff: {result['from']} → {result['to']}")
        print(f"  追加: {len(result['added'])} 件")
        print(f"  削除: {len(result['removed'])} 件")
        print(f"  変更: {len(result['changed'])} 件")
        print(f"  → {out}")
