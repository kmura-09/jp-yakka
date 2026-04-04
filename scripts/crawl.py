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

# 既知のページURLパターン。年度ごとにパスが変わるので複数候補を試す。
def candidate_urls() -> list[str]:
    year = datetime.now().year
    urls = []
    for y in [year, year - 1]:
        for month in ["04", "06", "10", "12", "03"]:
            urls.append(f"{BASE}/topics/{y}/{month}/")
    return urls


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
        # 自動探索
        detail_urls = []
        seen = set()
        for base_url in candidate_urls():
            for link in find_excel_links(base_url):
                if link not in seen:
                    seen.add(link)
                    detail_urls.append(link)
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

    # 同じ収載日ごとにまとめてパース
    import subprocess
    from itertools import groupby

    def version_key(p):
        m = re.search(r'tp(\d{8})', p.name)
        return m.group(1) if m else ""

    for ver, group in groupby(sorted(downloaded, key=version_key), key=version_key):
        files = [str(p) for p in group]
        subprocess.run(
            ["python3", "scripts/parse_excel.py"] + files + [str(data_dir)],
            check=True,
        )

    print(f"\n完了: {len(downloaded)} ファイル処理")
