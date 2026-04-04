#!/usr/bin/env python3
"""厚労省の薬価基準ExcelをJSONに変換する"""

import json
import sys
import re
from pathlib import Path
import openpyxl


def normalize(val):
    if val is None:
        return ""
    # 全角スペースや余白を除去
    return str(val).strip()


def parse_excel(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    records = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        kubun    = normalize(row[0])
        code     = normalize(row[1])
        seibun   = normalize(row[2])
        kikaku   = normalize(row[3])
        hinmei   = normalize(row[7])
        maker    = normalize(row[8])
        kouhatsu = normalize(row[9])   # 後発品 / ★ / ""
        senpatu  = normalize(row[10])  # 先発品 / 準先発品 / ""
        maru     = normalize(row[11])  # ○ = 後発品と同額水準の先発品
        yakka    = row[12]
        limit    = normalize(row[13])  # 経過措置期限

        if not code:
            continue

        records.append({
            "kubun":    kubun,
            "code":     code,
            "seibun":   seibun,
            "kikaku":   kikaku,
            "hinmei":   hinmei,
            "maker":    maker,
            "kouhatsu": kouhatsu,
            "senpatu":  senpatu,
            "dougaku":  maru == "○",   # 先発と後発が同額水準
            "yakka":    float(yakka) if yakka is not None else None,
            "limit":    limit,
        })

    wb.close()
    return records


def extract_version(filename: str) -> str:
    # tp20260401-01_01.xlsx → 20260401
    m = re.search(r'tp(\d{8})', filename)
    return m.group(1) if m else "unknown"


if __name__ == "__main__":
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tp20260401-01_01.xlsx")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("docs/data")

    version = extract_version(input_path.name)
    records = parse_excel(input_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"yakka_{version}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"version": version, "records": records}, f, ensure_ascii=False, separators=(",", ":"))

    print(f"✓ {len(records)} 件 → {out}")
