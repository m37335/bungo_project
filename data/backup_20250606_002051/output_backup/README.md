# 出力ファイル構成 (Output Files)

このフォルダには文豪ゆかり地図システムが生成する各種出力ファイルが保存されています。

## 📂 **現在のアクティブファイル**

### CSV形式エクスポート
- `bungo_combined_20250605_094954.csv` - **最新の統合データ**（26KB, 153件）
- `bungo_analysis.csv` - 分析用データセット（24KB, 136件）

### GeoJSON形式エクスポート
- `bungo_production_export.geojson` - **本番環境データ**（142KB, 3283行）
- `bungo_places.geojson` - 標準地名データ（124KB, 2773行）

### 統計・メタデータ
- `bungo_stats.json` - データ統計情報（842B, 40行）

## 🗄️ **アーカイブファイル**

`archived/` フォルダには以下が保存されています：
- 開発・テスト用の古いCSVファイル（28ファイル）
- S3実験用データファイル
- タイムスタンプ付きエクスポート履歴

## 📋 **ファイル命名規則**

### CSVエクスポート
```
bungo_export_YYYYMMDD_HHMMSS_[type].csv
- authors: 作家データ
- works: 作品データ  
- places: 地名データ（全件）
- places_geocoded: ジオコーディング済み地名
- combined: 統合データ（推奨）
```

### GeoJSONエクスポート
```
bungo_[environment]_export.geojson
- production: 本番データ
- places: 標準地名データ
```

## 🔄 **自動生成について**

これらのファイルは以下のスクリプトにより自動生成されます：
- **CSV**: `src/export/export_csv.py` 
- **GeoJSON**: `src/export/export_geojson.py`
- **統計**: データベース更新時に自動計算

## ⚠️ **注意事項**

- 古いエクスポートファイルは定期的に`archived/`に移動してください
- 本番使用時は最新のタイムスタンプ付きファイルを確認してください
- アーカイブファイルは参考用として保持されていますが、削除可能です

---
最終更新: 2025年6月6日 