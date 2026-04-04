#!/usr/bin/env python3
"""
成分名+規格でグルーピングして先発品・後発品を横並びにした比較JSONを生成する。
後発品が存在する先発品のみ対象。
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build(records):
    # 成分名+規格 でグループ化
    groups = defaultdict(lambda: {"senpatu": [], "kouhatsu": []})

    for r in records:
        key = (r["seibun"], r["kikaku"], r["kubun"])
        if r["senpatu"] in ("先発品", "準先発品"):
            groups[key]["senpatu"].append(r)
        elif r["kouhatsu"] in ("後発品", "★"):
            groups[key]["kouhatsu"].append(r)

    rows = []
    for (seibun, kikaku, kubun), g in groups.items():
        if not g["senpatu"] or not g["kouhatsu"]:
            continue  # 先発か後発のどちらかしかない成分は除外

        kouhatsu_yakkas = [r["yakka"] for r in g["kouhatsu"] if r["yakka"] is not None]
        if not kouhatsu_yakkas:
            continue

        min_kouhatsu = min(kouhatsu_yakkas)
        max_kouhatsu = max(kouhatsu_yakkas)

        for s in g["senpatu"]:
            if s["yakka"] is None:
                continue
            diff = s["yakka"] - min_kouhatsu
            rows.append({
                "kubun":         kubun,
                "seibun":        seibun,
                "kikaku":        kikaku,
                "senpatu_hinmei": s["hinmei"],
                "senpatu_maker":  s["maker"],
                "senpatu_yakka":  s["yakka"],
                "senpatu_type":   s["senpatu"],
                "kouhatsu_count": len(g["kouhatsu"]),
                "kouhatsu_min":   round(min_kouhatsu, 1),
                "kouhatsu_max":   round(max_kouhatsu, 1),
                "diff":           round(diff, 1),   # 先発 - 最安後発（正=先発が高い）
                "dougaku":        round(diff, 1) == 0.0,  # 先発と最安後発が同額
                "kouhatsu_list":  sorted(
                    [{"hinmei": r["hinmei"], "maker": r["maker"], "yakka": r["yakka"]}
                     for r in g["kouhatsu"] if r["yakka"] is not None],
                    key=lambda x: x["yakka"]
                ),
            })

    # 差額降順（先発が高いほど上）
    rows.sort(key=lambda r: -r["diff"])
    return rows


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/data")

    for json_path in sorted(data_dir.glob("yakka_*.json")):
        data = load(json_path)
        rows = build(data["records"])
        out = data_dir / f"compare_{data['version']}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"version": data["version"], "rows": rows}, f,
                      ensure_ascii=False, separators=(",", ":"))
        print(f"✓ {json_path.name} → {out.name}  ({len(rows)} 件)")
