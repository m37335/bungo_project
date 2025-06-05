# 文豪ゆかり地図システム (Bungo Places Map)

**青空文庫から文豪作品の地名を自動抽出し、地図データとして可視化するシステム**

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![GiNZA](https://img.shields.io/badge/NLP-GiNZA-green.svg)](https://megagonlabs.github.io/ginza/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 **クイックスタート（一気通貫実行）**

### **💨 最速実行（推奨）**
```bash
# リポジトリクローン
git clone https://github.com/m37335/bungo_project.git
cd bungo_project

# 一気通貫実行（20作家、最大10作品/作家）
./run_full_pipeline.sh

# または手動実行
python scripts/full_pipeline.py --max-works 15 --verbose
```

### **📊 実行結果**
- **処理時間**: 20-60分（作品数により変動）
- **対象作家**: 20名（夏目漱石、太宰治、与謝野晶子等）
- **期待出力**: 
  - 統合CSVデータ（`data/output/bungo_export_*_combined.csv`）
  - 地図用GeoJSON（`data/output/bungo_production_export_*.geojson`）
  - 統計レポート（`data/output/pipeline_report_*.json`）

### **⚡ 要件**
```bash
pip install -r requirements.txt
```
- Python 3.7+
- spaCy + ja-ginza（日本語NLP）
- SQLite（データベース）
- インターネット接続（青空文庫API・ジオコーディング）

---

## 📖 **詳細説明**

### システム概要

文豪作品から地名を自動抽出し、位置情報付きデータとして可視化するためのエンドツーエンドシステムです。

### 主要機能

📚🗾 日本の文豪作品から地名を抽出し、地図上に可視化するシステム

## 🎯 概要

文豪ゆかり地図システムは、青空文庫の作品テキストから自然言語処理技術を使って地名を抽出し、ジオコーディングによって地図上に可視化するプロジェクトです。文学と地理の交点を探求し、作品の舞台となった場所を発見できます。

## ✨ 主要機能

### 📖 データ収集・解析
- **青空文庫API連携**: 19,355作品のカタログから自動ダウンロード
- **GiNZA自然言語処理**: 高精度地名抽出（正規表現ベース）
- **自動ジオコーディング**: Nominatim API使用、100%成功率達成

### 🗺️ 地図可視化
- **GeoJSONエクスポート**: MapKit/Leaflet対応形式
- **CSVデータ出力**: 5種類（作者/作品/地名/統合/全件）
- **座標データ完備**: 緯度経度・住所・信頼度情報

### 🔍 高速検索
- **作者検索**: あいまい検索対応（<0.002秒）
- **作品検索**: 地名一覧付き詳細表示
- **地名検索**: 作者・作品逆引き機能

### 🌐 REST API
- **FastAPI実装**: OpenAPI仕様準拠
- **GPT関連度判定**: OpenAI API連携（S5機能）
- **エンドポイント**: 検索/統計/エクスポート/GPT判定

## 📊 現在のデータ状況（2025年6月5日時点）

```
📈 データベース統計
==============================
👤 作者数: 15名（日本文学の巨匠たち）
📚 作品数: 42作品（青空文庫から収集済み）
🗺️ 地名数: 109箇所（文学作品から抽出）
📍 ジオコーディング率: 100.0%
✅ ジオコーディング済み: 109箇所
```

### 📚 収録作家
- **明治時代**: 夏目漱石、森鴎外、樋口一葉、正岡子規
- **大正時代**: 芥川龍之介、与謝野晶子、石川啄木
- **昭和時代**: 太宰治、川端康成、三島由紀夫、宮沢賢治
- **現代文学**: 中島敦、谷崎潤一郎、志賀直哉、武者小路実篤

## 🛠️ 技術スタック

### バックエンド
- **Python 3.7+**: メインプログラミング言語
- **SQLite**: 構造化データベース（3階層設計）
- **GiNZA**: 日本語自然言語処理ライブラリ
- **FastAPI**: REST API フレームワーク

### データ処理
- **pandas**: データ分析・CSV処理
- **requests**: HTTP通信（青空文庫API）
- **geopy**: ジオコーディング（Nominatim）
- **openai**: GPT関連度判定（オプション）

### 可視化・出力
- **GeoJSON**: 地図可視化標準フォーマット
- **CSV**: データ分析・Excel連携
- **JSON**: 統計情報・メタデータ

## 🚀 クイックスタート

### 1. セットアップ
```bash
# リポジトリクローン
git clone https://github.com/[username]/bungo_project.git
cd bungo_project

# 仮想環境作成
python -m venv venv_ginza
source venv_ginza/bin/activate  # macOS/Linux
# venv_ginza\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 2. データベース初期化
```bash
# テストデータベース使用
python src/core/search.py stats

# 本番データベース使用
python src/core/search.py --db data/bungo_production.db stats
```

### 3. 基本的な使用方法
```bash
# 作者検索
python src/core/search.py author "夏目漱石"

# 作品検索（地名付き）
python src/core/search.py work "草枕"

# 地名検索（逆引き）
python src/core/search.py place "京都"

# データエクスポート
python src/export/export_csv.py --type all
python src/export/export_geojson.py

# データ収集パイプライン実行
python scripts/collect.py --author "太宰治" --max-works 3
```

## 📁 プロジェクト構成

```
bungo_project/
├── 📂 src/                     # ソースコード（機能別整理）
│   ├── 🧠 core/                # コア機能
│   │   ├── db_utils.py         # データベース操作・SQLite管理
│   │   ├── search.py           # 高速検索CLI（<0.002秒）
│   │   ├── aozora_fetcher.py   # 青空文庫API連携・ダウンロード
│   │   ├── aozora_place_extract.py # GiNZA地名抽出エンジン
│   │   ├── aozora_utils.py     # 青空文庫ユーティリティ
│   │   └── geocode_utils.py    # ジオコーディング（Nominatim API）
│   │
│   ├── 🌐 api/                 # REST API・Web関連
│   │   ├── api_server.py       # FastAPI REST API（OpenAPI準拠）
│   │   └── gpt_relevance_service.py # GPT関連度判定サービス
│   │
│   ├── 📤 export/              # データエクスポート
│   │   ├── export_csv.py       # CSV出力（5種類対応）
│   │   └── export_geojson.py   # GeoJSON出力（地図可視化用）
│   │
│   ├── 🔧 utils/               # ユーティリティ・ツール
│   │   ├── add_authors.py      # 作者追加スクリプト
│   │   ├── fix_encoding.py     # 文字化け修正ツール
│   │   ├── migrate_legacy_data.py # データ移行ツール
│   │   ├── run_full_migration.py # 一括移行実行
│   │   ├── bungo_sheets_integration.py # Google Sheets連携
│   │   └── bungo_work_map_enhanced.py # 拡張地図機能
│   │
│   └── 🧪 tests/               # テストスイート
│       ├── test_ginza_pipeline.py # GiNZAパイプラインテスト
│       ├── test_csv_export.py  # CSVエクスポートテスト
│       ├── test_s3_export.py   # S3エクスポートテスト
│       ├── test_s4_search.py   # S4検索機能テスト
│       ├── test_s5_api.py      # S5 APIテスト
│       └── test_kusamakura.py  # 草枕処理テスト
│
├── 📊 data/                    # データ・キャッシュ
│   ├── bungo_production.db     # 本番データベース（15作家・109地名）
│   ├── test_ginza.db           # テスト用データベース
│   ├── geocode_cache.json      # ジオコーディングキャッシュ
│   ├── aozora_cache/           # 青空文庫テキストキャッシュ
│   ├── output/                 # エクスポートファイル出力先
│   └── test_output/            # テスト出力ディレクトリ
│
├── 📚 docs/                    # ドキュメント・仕様書
│   ├── s3_completion_report.md # S3完了報告書
│   ├── s4_completion_report.md # S4完了報告書  
│   ├── s5_completion_report.md # S5完了報告書
│   └── s5_openapi_spec.yaml    # OpenAPI仕様書
│
├── 🚀 scripts/                 # CLIスクリプト・実行ファイル
│   ├── collect.py              # データ収集パイプライン
│   └── bungo_cli.py           # 統合CLI管理ツール
│
├── ⚙️ 設定・ドキュメント
│   ├── README.md               # プロジェクト説明（本ファイル）
│   ├── LICENSE                 # MITライセンス
│   ├── TODO_PROGRESS.md        # 進捗管理
│   ├── db_schema.sql           # SQLiteスキーマ定義
│   ├── requirements.txt        # 基本依存関係
│   ├── requirements_ginza.txt  # GiNZA依存関係
│   ├── requirements_latest.txt # 最新版依存関係
│   ├── requirements_minimal.txt # 最小依存関係
│   ├── .gitignore             # Git除外設定
│   ├── .python-version        # Python版本指定
│   ├── .env                   # 環境変数設定
│   └── credentials.json       # API認証情報
│
└── 📈 データファイル（生成物）
    ├── bungo_enhanced_*.csv    # 拡張データセット
    ├── migrated_bungo_data.csv # 移行済みデータ
    └── __pycache__/           # Python キャッシュ
```

### 🏗️ **新フォルダ構造の特徴**

#### **📂 src/ - 機能別モジュール設計**
- **論理的分離**: 機能ごとに明確に分類
- **保守性向上**: 関連ファイルが近接配置
- **スケーラビリティ**: 新機能追加が容易

#### **📊 data/ - データ集約管理**  
- **一元管理**: DB・キャッシュ・出力を統合
- **バックアップ効率**: データディレクトリのみ対象
- **アクセス制御**: データアクセスパターン最適化

#### **📚 docs/ - 文書体系化**
- **技術文書**: 完了報告書・API仕様書
- **履歴管理**: スプリント進捗の可視化
- **開発ガイド**: 新規開発者向けリソース

#### **🚀 scripts/ - 実行環境整備**
- **CLI統合**: ユーザー向け実行スクリプト
- **自動化**: バッチ処理・データ収集パイプライン
- **運用支援**: 本番環境での実行サポート

## 🔧 高度な使用方法

### データ収集パイプライン
```bash
# 特定作者の全作品収集
python scripts/collect.py --author "芥川龍之介" --max-works 10

# 全作者一括収集（本番実行）
python scripts/collect.py --all --max-works 5 --verbose

# GiNZAパイプラインテスト実行
python src/tests/test_ginza_pipeline.py
```

### 検索・データベース操作
```bash
# 高速検索CLI実行
python src/core/search.py author "夏目漱石"
python src/core/search.py work "草枕"
python src/core/search.py place "京都"

# データベース統計表示
python src/core/search.py --db data/bungo_production.db stats
```

### エクスポート機能
```bash
# CSV形式エクスポート（5種類）
python src/export/export_csv.py --type all --output data/output/

# GeoJSON形式エクスポート（地図可視化用）
python src/export/export_geojson.py --db data/bungo_production.db --output data/output/bungo_latest.geojson

# 統合CLI経由
python scripts/bungo_cli.py export --format csv
python scripts/bungo_cli.py export --format geojson
```

### API サーバー起動
```bash
# 開発サーバー起動
pip install fastapi uvicorn
uvicorn src.api.api_server:app --host 0.0.0.0 --port 8000 --reload

# API ドキュメント
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### REST API エンドポイント例
```bash
# 統計取得
curl http://localhost:8000/stats

# 作者検索
curl "http://localhost:8000/search/authors?q=夏目漱石"

# CSVエクスポート
curl "http://localhost:8000/export/csv?export_type=combined"

# GeoJSONエクスポート
curl "http://localhost:8000/export/geojson"

# GPT関連度判定（要OpenAI API設定）
curl -X POST "http://localhost:8000/gpt/relevance" \
  -H "Content-Type: application/json" \
  -d '{"author": "夏目漱石", "work": "草枕", "place": "熊本"}'
```

### テスト実行
```bash
# 全テストスイート実行
cd src/tests/
python test_ginza_pipeline.py  # GiNZA地名抽出テスト
python test_csv_export.py      # CSVエクスポートテスト
python test_s4_search.py       # S4検索機能テスト
python test_s5_api.py          # S5 APIテスト

# 特定機能テスト
python test_kusamakura.py      # 草枕処理テスト
python test_s3_export.py       # S3エクスポートテスト
```

### ユーティリティツール
```bash
# 作者追加
python src/utils/add_authors.py --name "新作者名" --works "作品1,作品2"

# 文字化け修正
python src/utils/fix_encoding.py --input data/aozora_cache/ --fix-all

# データ移行
python src/utils/migrate_legacy_data.py --source old_data.csv --target data/bungo_production.db
python src/utils/run_full_migration.py  # 一括移行実行

# Google Sheets連携
python src/utils/bungo_sheets_integration.py --export --sheet-id YOUR_SHEET_ID
```

## 📁 出力ファイル一覧

### 🗂️ **データエクスポート出力先: `data/output/`**

#### **CSV形式エクスポート**
```
data/output/
├── bungo_export_YYYYMMDD_HHMMSS_authors.csv       # 作者データ
├── bungo_export_YYYYMMDD_HHMMSS_works.csv         # 作品データ  
├── bungo_export_YYYYMMDD_HHMMSS_places.csv        # 地名データ（全件）
├── bungo_export_YYYYMMDD_HHMMSS_places_geocoded.csv # 地名データ（ジオコーディング済み）
└── bungo_export_YYYYMMDD_HHMMSS_combined.csv      # 統合データ（推奨）
```

**combined.csv 詳細構造：**
```csv
author_name,birth_year,death_year,work_title,publication_year,genre,
place_name,latitude,longitude,address,sentence,before_text,after_text
```

#### **GeoJSON形式エクスポート**
```
data/output/
├── bungo_places.geojson                # 標準GeoJSON出力
├── bungo_production_export.geojson     # 本番データGeoJSON  
└── bungo_stats.json                    # 統計情報JSON
```

**GeoJSON構造例：**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [139.6917, 35.6895]
      },
      "properties": {
        "author_name": "夏目漱石",
        "work_title": "草枕",
        "place_name": "東京",
        "sentence": "東京の喧騒を離れて...",
        "maps_url": "https://maps.google.com/?q=35.6895,139.6917"
      }
    }
  ]
}
```

#### **データベースファイル**
```
data/
├── bungo_production.db     # 本番データベース（15作家・109地名）
├── test_ginza.db          # テスト用データベース
└── geocode_cache.json     # ジオコーディングキャッシュ
```

#### **レガシーファイル（ルート）**
```
bungo_project/
├── bungo_enhanced_work_places.csv    # 拡張地図データ（レガシー）
├── bungo_enhanced_japanese.csv       # 日本語ヘッダー版（レガシー）  
└── migrated_bungo_data.csv          # 移行済みデータ
```

## ⚙️ 高度なカスタマイズ

### 🎛️ **環境変数によるカスタマイズ**

#### **データ収集制御**
```bash
# 収集対象作家数制御
export MAX_AUTHORS=10          # 1-15名まで設定可能

# 作品数制御  
export MAX_WORKS_PER_AUTHOR=5  # 1作家あたりの最大作品数

# データベースパス指定
export DATABASE_PATH=data/bungo_production.db

# 出力ディレクトリ指定
export OUTPUT_DIR=data/output

# ジオコーディングAPI制御
export GEOCODING_DELAY=1.0     # リクエスト間隔（秒）
export GEOCODING_RETRY=3       # 失敗時リトライ回数
```

#### **OpenAI API設定（GPT関連度判定）**
```bash
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-4o-mini          # 使用モデル
export GPT_MAX_TOKENS=150                # 最大トークン数
export GPT_TEMPERATURE=0.3               # 創造性パラメータ
```

### 🔧 **設定ファイルカスタマイズ**

#### **作家リスト変更: `scripts/collect.py`**
```python
# 対象作家の追加・変更（76行目付近）
AVAILABLE_AUTHORS = [
    "夏目漱石", "芥川龍之介", "太宰治", "川端康成", "宮沢賢治",
    "樋口一葉", "森鴎外", "石川啄木", "与謝野晶子", "正岡子規",
    "島崎藤村", "国木田独歩", "泉鏡花", "徳田秋声", "田山花袋",
    "谷崎潤一郎", "志賀直哉", "武者小路実篤", "中島敦", "横光利一"
]
```

#### **地名抽出パターン: `src/core/aozora_place_extract.py`**
```python
# 地名パターンの追加・修正（45行目付近）
PLACE_PATTERNS = [
    r'[都道府県]{1}',           # 都道府県
    r'[市区町村]{1}',           # 市区町村  
    r'[一-龯]{2,4}[駅港]{1}',   # 駅・港
    r'[一-龯]{2,5}[山川河海]{1}', # 自然地形
    r'[一-龯]{3,}[神社寺院]{1}', # 宗教施設
    # カスタムパターンをここに追加
]
```

#### **エクスポート設定: `src/export/export_csv.py`**
```python
# CSV出力フィールドのカスタマイズ（194行目付近）
COMBINED_FIELDNAMES = [
    'author_name', 'birth_year', 'death_year',
    'work_title', 'publication_year', 'genre', 'aozora_url',
    'place_name', 'latitude', 'longitude', 'address',
    'sentence', 'before_text', 'after_text',
    # 'custom_field_1', 'custom_field_2'  # カスタムフィールド追加
]
```

### 🎨 **可視化カスタマイズ**

#### **地図スタイル設定**
```javascript
// Leaflet.js カスタマイズ例
const mapStyle = {
    color: '#3388ff',           // 地点色
    radius: 8,                  // 地点サイズ
    fillOpacity: 0.8,          // 不透明度
    weight: 2                   // 枠線太さ
};

// 作家別色分け
const authorColors = {
    "夏目漱石": "#ff6b6b",
    "芥川龍之介": "#4ecdc4", 
    "太宰治": "#45b7d1",
    "川端康成": "#96ceb4",
    "宮沢賢治": "#feca57"
};
```

#### **データフィルタリング**
```python
# 期間フィルタ例
START_YEAR = 1900
END_YEAR = 1950

# 地域フィルタ例  
TARGET_PREFECTURES = ["東京都", "神奈川県", "京都府", "大阪府"]

# 作品ジャンルフィルタ例
TARGET_GENRES = ["小説", "随筆", "詩歌"]
```

### 🔄 **パイプライン自動化**

#### **定期実行設定**
```bash
# crontabによる自動実行（毎日午前2時）
0 2 * * * cd /path/to/bungo_project && python scripts/collect.py --all --max-works 3

# systemdタイマー設定
sudo systemctl enable bungo-collect.timer
sudo systemctl start bungo-collect.timer
```

#### **バッチ処理スクリプト**
```bash
#!/bin/bash
# batch_process.sh - 一括処理スクリプト例

# データ収集
python scripts/collect.py --all --max-works 5 --verbose

# エクスポート実行
python src/export/export_csv.py --type all --output data/output/
python src/export/export_geojson.py --db data/bungo_production.db --output data/output/bungo_latest.geojson

# 統計レポート生成
python src/core/search.py --db data/bungo_production.db stats > data/output/daily_stats.txt

echo "バッチ処理完了: $(date)"
```

## 📈 開発履歴・スプリント

### ✅ 完了済みスプリント
- **S1**: データベース設計・SQLiteスキーマ構築
- **S2**: 青空文庫パイプライン・GiNZA地名抽出
- **S3**: ジオコーディング・GeoJSONエクスポート（100%成功）
- **S4**: 高速検索機能（<0.001秒、目標25倍達成）
- **S5**: GPT関連度判定・FastAPI REST API化

### 🎯 技術成果
- **検索性能**: 目標の25倍高速化達成
- **データ品質**: ジオコーディング100%成功率
- **スケーラビリティ**: 19,355作品対応可能
- **API化**: OpenAPI仕様準拠の本格REST API

## 🌏 可視化・活用例

### GeoJSON活用
```javascript
// Leaflet.jsでの地図表示例
fetch('/export/geojson')
  .then(response => response.json())
  .then(data => {
    L.geoJSON(data, {
      onEachFeature: function(feature, layer) {
        layer.bindPopup(`
          <h3>${feature.properties.author_name}</h3>
          <p>『${feature.properties.work_title}』</p>
          <p>${feature.properties.place_name}</p>
          <p>${feature.properties.sentence}</p>
        `);
      }
    }).addTo(map);
  });
```

### データ分析活用
```python
import pandas as pd
import sqlite3

# CSVデータ読み込み（新しいパス）
df = pd.read_csv('data/output/bungo_combined_latest.csv')

# 作者別地名分布
author_places = df.groupby('author_name')['place_name'].count()

# 都道府県別出現頻度
prefecture_freq = df['address'].str.extract(r'(\w+[都道府県])')[0].value_counts()

# データベース直接アクセス例
conn = sqlite3.connect('data/bungo_production.db')
df_db = pd.read_sql_query("""
    SELECT a.name as author_name, w.title as work_title, 
           p.name as place_name, p.latitude, p.longitude
    FROM authors a 
    JOIN works w ON a.id = w.author_id 
    JOIN places p ON w.id = p.work_id
""", conn)
conn.close()
```

### 🎯 **統合使用例**

#### **完全なワークフロー実行**
```bash
# 1. 新規作家データ収集
python scripts/collect.py --author "谷崎潤一郎" --max-works 3 --verbose

# 2. データベース統計確認
python src/core/search.py --db data/bungo_production.db stats

# 3. 全データエクスポート
python src/export/export_csv.py --db data/bungo_production.db --type all --output data/output/
python src/export/export_geojson.py --db data/bungo_production.db --output data/output/bungo_latest.geojson

# 4. 品質確認
python src/tests/test_csv_export.py
python src/tests/test_s4_search.py

# 5. 統計レポート生成
python -c "
from src.core.db_utils import BungoDatabase
db = BungoDatabase('sqlite', 'data/bungo_production.db')
stats = db.get_stats()
print(f'📊 総計: {stats[\"authors_count\"]}作家, {stats[\"works_count\"]}作品, {stats[\"places_count\"]}地名')
db.close()
"
```

#### **カスタム分析パイプライン**
```python
# custom_analysis.py - カスタム分析例
import pandas as pd
import sqlite3
from pathlib import Path

# データベース接続
conn = sqlite3.connect('data/bungo_production.db')

# 地域別作家分布分析
query = """
SELECT 
    SUBSTR(p.address, 1, 3) as prefecture,
    COUNT(DISTINCT a.id) as author_count,
    COUNT(DISTINCT w.id) as work_count,
    COUNT(p.id) as place_count
FROM places p
JOIN works w ON p.work_id = w.id
JOIN authors a ON w.author_id = a.id
WHERE p.latitude IS NOT NULL
GROUP BY prefecture
ORDER BY place_count DESC
LIMIT 10
"""

df_regional = pd.read_sql_query(query, conn)
print("🗾 都道府県別文豪ゆかり地分布（上位10位）")
print(df_regional)

# 時代別分析
query_era = """
SELECT 
    CASE 
        WHEN a.birth_year < 1850 THEN '幕末以前'
        WHEN a.birth_year < 1900 THEN '明治時代'
        WHEN a.birth_year < 1925 THEN '大正時代'
        ELSE '昭和以降'
    END as era,
    COUNT(DISTINCT a.id) as author_count,
    AVG(CAST(p.latitude AS FLOAT)) as avg_latitude,
    AVG(CAST(p.longitude AS FLOAT)) as avg_longitude
FROM authors a
JOIN works w ON a.id = w.author_id
JOIN places p ON w.id = p.work_id
WHERE a.birth_year IS NOT NULL AND p.latitude IS NOT NULL
GROUP BY era
ORDER BY era
"""

df_era = pd.read_sql_query(query_era, conn)
print("\n📅 時代別文豪活動地域")
print(df_era)

conn.close()
```

## 🔮 今後の展望

### 機能拡張計画
- [ ] **Webアプリケーション**: React/Vue.js フロントエンド
- [ ] **機械学習強化**: BERT/GPTによる地名抽出精度向上
- [ ] **時系列分析**: 作品年代×地名変遷の可視化
- [ ] **多言語対応**: 英訳作品での地名照合

### データ拡張
- [ ] **作家拡張**: 現代作家・詩人・評論家
- [ ] **ジャンル多様化**: 随筆・書簡・日記
- [ ] **関連データ**: 作家生没年・作品発表年・歴史的背景

### 技術改善
- [ ] **パフォーマンス**: PostgreSQL移行・インデックス最適化
- [ ] **信頼性**: 自動テスト・CI/CD環境構築
- [ ] **可視化**: 3D地図・時系列アニメーション

## 🤝 コントリビューション

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🙏 謝辞

- **青空文庫**: パブリックドメイン作品の提供
- **国立情報学研究所**: GiNZA自然言語処理ライブラリ
- **OpenStreetMap**: Nominatimジオコーディングサービス
- **文学界の巨匠たち**: 時代を超えた作品の創造

---

**📚 文学と技術の融合で、新しい読書体験を創造する 🗾** 