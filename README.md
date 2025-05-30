# 日本の文豪情報収集・整理システム

このシステムは、WikipediaおよびOpenAI APIを活用して、日本の文豪に関する情報（代表作、所縁の土地）を自動で収集・整理し、CSVファイルやGoogle Sheetsに出力するツールです。

## 機能

- 🔍 **作家一覧の自動取得**: Wikipediaから日本の文豪リストを収集
- 📖 **Wikipedia情報取得**: 各作家のページから詳細情報を抽出
- 🤖 **AI補完**: OpenAI APIで情報を補完・整理
- 📊 **データ出力**: CSV形式およびGoogle Sheetsへの出力

## 必要条件

- Python 3.7以上
- OpenAI APIキー（オプション、より良い結果のため推奨）
- Google Service Account認証ファイル（Google Sheets出力用、オプション）

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境設定

#### 環境変数ファイルの作成
`env_example.txt`を参考に`.env`ファイルを作成：

```env
# OpenAI API キー（オプション）
OPENAI_API_KEY=your_openai_api_key_here

# Google Sheets設定用（オプション）
GOOGLE_CREDENTIALS_PATH=credentials.json

# 処理する文豪の最大数
MAX_AUTHORS=25
```

#### OpenAI APIキーの設定（オプション）
1. [OpenAI Platform](https://platform.openai.com/)でアカウント作成
2. APIキーを生成
3. `.env`ファイルに設定

#### Google Sheets設定（オプション）
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. Google Sheets API、Google Drive APIを有効化
3. サービスアカウントを作成し、認証ファイル（credentials.json）をダウンロード
4. プロジェクトディレクトリに配置

## 使用方法

### 基本的な実行

```bash
python bungo_collector.py
```

### テスト実行（少数の作家で試す）

```bash
python test_bungo.py
```

## 出力ファイル

### CSV出力
- ファイル名: `authors.csv`
- 列: 作家名、代表作、所縁の地

### Google Sheets
- シート名: "日本文豪データ"
- 自動で共有リンクが生成されます

## システム構成

```
bungo_project/
├── bungo_collector.py     # メインシステム
├── test_bungo.py         # テスト用スクリプト
├── requirements.txt      # 依存関係
├── env_example.txt       # 環境変数サンプル
├── .env                  # 環境変数（作成必要）
├── credentials.json      # Google認証ファイル（作成必要）
└── README.md            # このファイル
```

## 主な処理フロー

1. **文豪一覧取得**: Wikipediaカテゴリ + 手動リストから作家名を収集
2. **Wikipedia本文取得**: 各作家のページ内容を取得
3. **情報抽出**: 正規表現で作品名・地名を抽出
4. **AI補完**: OpenAI APIで情報を整理・補完（オプション）
5. **データ整形**: pandas DataFrameに変換
6. **出力**: CSV・Google Sheetsに保存

## 注意事項

- **API制限**: OpenAI APIには利用料金がかかります
- **処理時間**: 50名の文豪で約30-60分程度
- **Wikipedia負荷**: 1秒間隔でアクセス制限を設けています
- **データ品質**: 自動抽出のため、一部不正確な情報が含まれる可能性があります

## カスタマイズ

### 処理対象の変更
`famous_authors`リストや`max_authors`設定で対象を調整可能

### 抽出条件の変更
`extract_works_and_places`メソッドで正規表現パターンを調整

### AI補完プロンプトの変更
`enhance_with_ai`メソッド内のプロンプトを編集

## トラブルシューティング

### よくあるエラー

1. **ModuleNotFoundError**: `pip install -r requirements.txt`を実行
2. **OpenAI API Error**: APIキーの確認、残高の確認
3. **Google Sheets Error**: 認証ファイルのパス、権限の確認
4. **Wikipedia Error**: インターネット接続、一時的なアクセス制限

### デバッグ方法

1. まず`test_bungo.py`で小規模テスト
2. ログメッセージで進捗確認
3. 環境変数の確認（`.env`ファイル）

## 今後の拡張予定

- 🗺️ 地図連携機能
- 📅 時代別フィルタ
- 🎨 Web UI（Streamlit）
- 📚 青空文庫連携
- 🔍 検索・フィルタ機能

## ライセンス

MIT License

## 貢献

バグ報告や機能提案はIssueにてお願いします。

---

*注意: このツールは教育・研究目的で作成されています。商用利用の際は利用規約をご確認ください。* 