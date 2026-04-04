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
    # 引数: 入力ファイル(複数可) [出力ディレクトリ]
    # 同じ収載日(_01〜_04)のファイルをまとめて1つのJSONにする
    args = sys.argv[1:]
    if not args:
        args = sorted(Path(".").glob("tp20260401-01_0?.xlsx"))

    # 出力ディレクトリは末尾引数がディレクトリ指定の場合
    output_dir = Path("docs/data")
    input_paths = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            output_dir = p
        else:
            input_paths.append(p)

    if not input_paths:
        print("入力ファイルが見つかりません")
        sys.exit(1)

    # バージョンは最初のファイル名から取得
    version = extract_version(input_paths[0].name)

    all_records = []
    for p in sorted(input_paths):
        recs = parse_excel(p)
        all_records.extend(recs)
        print(f"  {p.name}: {len(recs)} 件")

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"yakka_{version}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"version": version, "records": all_records}, f, ensure_ascii=False, separators=(",", ":"))

    print(f"✓ 合計 {len(all_records)} 件 → {out}")
