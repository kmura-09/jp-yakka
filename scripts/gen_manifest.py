#!/usr/bin/env python3
"""docs/data/ をスキャンして manifest.json を生成する。

index.html はこの manifest を読んでバージョン一覧（薬価一覧・先発後発比較・改定差分）を
動的に構築するため、データファイルを追加してもHTMLを手で書き換える必要がなくなる。
"""

import json
import re
import sys
from pathlib import Path


def label_of(d: str) -> str:
    """'20260401' -> '2026年4月1日'"""
    return f"{int(d[0:4])}年{int(d[4:6])}月{int(d[6:8])}日"


def main() -> None:
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/data")
    names = {p.name for p in data_dir.glob("*.json")}

    # 薬価一覧（新しい日付が上）
    versions = []
    for name in sorted(names, reverse=True):
        m = re.fullmatch(r"yakka_(\d{8})\.json", name)
        if m:
            versions.append({"label": label_of(m.group(1)), "file": f"data/{name}"})

    # 先発・後発比較（compare_delta_* は対応する compare_ の deltaFile として紐づける）
    compares = []
    for name in sorted(names, reverse=True):
        m = re.fullmatch(r"compare_(\d{8})\.json", name)
        if not m:
            continue
        d = m.group(1)
        delta = next(
            (f"data/{n}" for n in names if re.fullmatch(rf"compare_delta_\d{{8}}_{d}\.json", n)),
            None,
        )
        compares.append({"label": label_of(d), "file": f"data/{name}", "deltaFile": delta})

    # 改定前後の差分
    diffs = []
    for name in sorted(names, reverse=True):
        m = re.fullmatch(r"diff_(\d{8})_(\d{8})\.json", name)
        if m:
            diffs.append({
                "label": f"{label_of(m.group(1))} → {label_of(m.group(2))}",
                "file": f"data/{name}",
            })

    manifest = {"versions": versions, "compares": compares, "diffs": diffs}
    out = data_dir / "manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest.json: {len(versions)} versions, {len(compares)} compares, {len(diffs)} diffs")


if __name__ == "__main__":
    main()
