# レガシーアーカイブ (Legacy Archive)

このフォルダには文豪ゆかり地図システム開発過程で使用されていたが、現在はアクティブでないファイルが保管されています。

## 📁 フォルダ構成

### `data/` - レガシーデータファイル
- `bungo_enhanced_work_places.csv` - 旧形式の拡張地図データ（136件）
- `bungo_enhanced_japanese.csv` - 日本語ヘッダー版データ（82件）  
- `migrated_bungo_data.csv` - データ移行用ファイル（136件）

### `docs/` - 古いドキュメント
- `TODO_PROGRESS.md` - 旧進捗管理ファイル（開発履歴として保存）

### `archived_scripts/` - 使用終了スクリプト・設定
- `bungo_work_map_enhanced.py` - 拡張地図機能（567行、27KB）
- `bungo_sheets_integration.py` - Google Sheets連携（416行、16KB）
- `migrate_legacy_data.py` - データ移行ツール（238行、8.7KB）
- `run_full_migration.py` - 一括移行実行（30行、997B）
- `requirements_ginza.txt` - GiNZA専用依存関係（旧版）
- `requirements_latest.txt` - 最新版依存関係（旧版）
- `requirements_minimal.txt` - 最小依存関係（旧版）

## 🚫 **注意事項**

- これらのファイルは**アーカイブ目的**で保存されています
- 現在のシステムでは使用されていません
- 削除前の一時保管として利用してください
- 参考として必要な場合のみアクセスしてください

## 🔄 **現在のアクティブなコード**

最新のシステムは以下の場所にあります：
- **メインコード**: `../src/` (core, api, export, utils, tests)
- **現在のデータ**: `../data/` (bungo_production.db, output/, etc.)
- **実行スクリプト**: `../scripts/`
- **ドキュメント**: `../docs/`
- **依存関係**: `../requirements.txt` (最適化済み), `../requirements-optional.txt` (オプション機能)

---
アーカイブ日: 2025年6月5日 