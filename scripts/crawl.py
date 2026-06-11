#!/usr/bin/env python3
"""
厚労省の薬価基準ページからExcelをダウンロードし、JSONに変換する。
URL体系: https://www.mhlw.go.jp/topics/YYYY/04/tp{YYYYMMDD}-01.html
改定は年4回程度（4月・6月・10月・12月）なので月1回実行で十分。
"""

import re
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

BASE = "https://www.mhlw.go.jp"

# 薬価基準収載品目ページのURL候補。年度ごとに /topics/{y}/04/tp{y}0401-01.html に置かれる。
def candidate_urls() -> list[str]:
    year = datetime.now().year
    return [f"{BASE}/topics/{y}/04/tp{y}0401-01.html" for y in [year, year - 1]]


def find_excel_links(page_url: str) -> list[str]:
    """薬価基準ページからExcelファイルのURLを抽出する"""
    try:
        with urllib.request.urlopen(page_url, timeout=10) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception:
        return []

    # tp20260401-01.html のようなリンクを探す
    links = re.findall(r'href="([^"]*tp\d{8}-01[^"]*\.html)"', html)
    full = [l if l.startswith("http") else BASE + l for l in links]
    return full


def find_excel_on_detail(detail_url: str) -> list[str]:
    """詳細ページからExcel(.xlsx)リンクを抽出する"""
    try:
        with urllib.request.urlopen(detail_url, timeout=10) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception:
        return []

    links = re.findall(r'href="([^"]*\.xlsx)"', html)
    full = [l if l.startswith("http") else BASE + l for l in links]
    # _01〜_04: 内用薬・注射薬・外用薬・歯科用薬剤
    main = [l for l in full if re.search(r'tp\d{8}-01_0[1-4]\.xlsx', l)]
    return main if main else []


def download(url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  skip (already exists): {dest.name}")
        return False
    print(f"  download: {url}")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"  error: {e}")
        return False


if __name__ == "__main__":
    xlsx_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    data_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("docs/data")
    xlsx_dir.mkdir(parents=True, exist_ok=True)

    # 直接URLが渡された場合（Actions等からの呼び出し）
    if len(sys.argv) > 3:
        detail_urls = sys.argv[3:]
    else:
        # 自動探索: 候補ページ(今年→去年)を順に見て、最初にxlsxが取れたページだけを使う。
        # 去年のページも併用すると旧年度の不完全な版が混入するため、現行ページに限定する。
        detail_urls = next(([u] for u in candidate_urls() if find_excel_on_detail(u)), [])
        if not detail_urls:
            print("対象ページが見つかりませんでした")
            sys.exit(1)

    downloaded = []
    for detail_url in detail_urls:
        print(f"検索: {detail_url}")
        excel_links = find_excel_on_detail(detail_url)
        for url in excel_links:
            fname = re.search(r'(tp\d{8}-01_0[1-4]\.xlsx)', url)
            if not fname:
                continue
            dest = xlsx_dir / fname.group(1)
            if download(url, dest):
                downloaded.append(dest)

    if not downloaded:
        print("新しいファイルはありませんでした")
        sys.exit(0)

    # 内用・注射・外用・歯科(_01〜_04)を1つの収載版としてまとめてパースする。
    # 歯科用(_04)は改定が無い間は旧日付で据え置かれるが、最新の収載版の一部として扱う。
    # 日付ごとに分割すると歯科だけの不完全な版ができてしまうため、まとめて1ファイルにする。
    import subprocess
    files = [str(p) for p in sorted(downloaded)]
    subprocess.run(
        ["python3", "scripts/parse_excel.py"] + files + [str(data_dir)],
        check=True,
    )

    print(f"\n完了: {len(downloaded)} ファイル処理")
