# jp-yakka

厚生労働省が公開する薬価基準データを、ブラウザで検索・フィルタできる静的サイトです。

**https://kmura-09.github.io/jp-yakka/**

## 機能

- 品名・成分名・メーカー名での全文検索
- 区分（内用薬 / 外用薬 / 注射薬）でのフィルタ
- 種別（先発品 / 準先発品 / 後発品 / ★加算対象外）でのフィルタ
- 後発品と同額水準（○）の先発品に絞り込み
- 各列でのソート
- 収載バージョンの切り替え（改定前後の比較）

## データソース

[厚生労働省 薬価基準収載品目リスト](https://www.mhlw.go.jp/topics/2026/04/tp20260401-01.html)

毎月1日に GitHub Actions が自動クロールし、新しい改定データがあれば自動更新します。

## 種別バッジの意味

| バッジ | 意味 |
|---|---|
| 先発品 | 新薬として最初に承認された医薬品 |
| 準先発品 | 後発品制度以前（1967年以前）から収載されている先発品 |
| 後発品 | 診療報酬の加算・変更調剤の対象となるジェネリック |
| 後発品★ | 後発品だが先発品と同額以上のため加算対象外 |
| ○同額 | 後発品と同額水準まで薬価が下がった先発品（長期収載品G1等） |

## 構成

```
docs/           GitHub Pages 公開ディレクトリ
  index.html    フロントエンド（vanilla JS）
  data/         パース済みJSON（改定ごとに追加）

scripts/
  crawl.py      厚労省ページからExcelを取得
  parse_excel.py ExcelをJSONに変換

.github/workflows/
  crawl.yml     月次自動更新
```

## ローカルで動かす

```bash
pip install openpyxl

# データ更新（手動）
python3 scripts/crawl.py

# 確認
python3 -m http.server 8765 --directory docs
# → http://localhost:8765/
```
