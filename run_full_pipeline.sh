#!/bin/bash

# 文豪ゆかり地図システム - 一気通貫実行スクリプト
# 全作家の最大作品数での完全パイプライン実行

set -e  # エラー時に停止

echo "🚀 文豪ゆかり地図システム - 完全パイプライン実行"
echo "================================================"

# プロジェクトルートへ移動
cd "$(dirname "$0")"

# PYTHONPATH設定
export PYTHONPATH="$PWD/src/core:$PWD/src/export:$PWD/src/utils:$PYTHONPATH"

# デフォルト設定
MAX_WORKS=10
BACKUP=true
VERBOSE=false

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-works)
            MAX_WORKS="$2"
            shift 2
            ;;
        --no-backup)
            BACKUP=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "使用方法: $0 [オプション]"
            echo ""
            echo "オプション:"
            echo "  --max-works N     作家あたりの最大作品数 (デフォルト: 10)"
            echo "  --no-backup       既存データのバックアップをスキップ"
            echo "  --verbose         詳細ログ出力"
            echo "  --help, -h        このヘルプを表示"
            echo ""
            echo "実行例:"
            echo "  $0                    # 基本実行"
            echo "  $0 --max-works 15     # 最大15作品/作家"
            echo "  $0 --verbose          # 詳細ログ付き"
            exit 0
            ;;
        *)
            echo "未知のオプション: $1"
            echo "ヘルプは $0 --help で確認してください"
            exit 1
            ;;
    esac
done

# 設定表示
echo "📋 実行設定:"
echo "   最大作品数: ${MAX_WORKS}/作家"
echo "   バックアップ: $([[ $BACKUP == true ]] && echo "有効" || echo "無効")"
echo "   詳細ログ: $([[ $VERBOSE == true ]] && echo "有効" || echo "無効")"
echo ""

# 依存関係チェック
echo "🔍 依存関係チェック中..."
if ! python -c "import spacy, pandas, requests, geopy" 2>/dev/null; then
    echo "❌ 必要なライブラリが不足しています"
    echo "📦 インストール中..."
    pip install -r requirements.txt
fi

echo "✅ 依存関係OK"
echo ""

# 実行確認
echo "⚠️  この処理は時間がかかります（推定: 20-60分）"
echo "   処理対象: 20名の主要作家"
echo "   最大作品数: ${MAX_WORKS}/作家"
echo ""
read -p "実行しますか？ [y/N]: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 実行がキャンセルされました"
    exit 0
fi

# パイプライン実行
echo ""
echo "🚀 完全パイプライン実行開始..."
echo "================================================"

# 引数構築
ARGS="--max-works $MAX_WORKS"
if [[ $BACKUP == false ]]; then
    ARGS="$ARGS --no-backup"
fi
if [[ $VERBOSE == true ]]; then
    ARGS="$ARGS --verbose"
fi

# 実行
if python scripts/full_pipeline.py $ARGS; then
    echo ""
    echo "🎉 完全パイプライン実行成功！"
    echo ""
    echo "📁 生成ファイル確認:"
    echo "   データベース: data/bungo_production.db"
    echo "   出力ファイル: data/output/"
    echo "   実行ログ: full_pipeline_*.log"
    echo ""
    echo "🌐 次のステップ:"
    echo "   - data/output/bungo_export_*_combined.csv (統合データ)"
    echo "   - data/output/bungo_production_export_*.geojson (地図データ)"
    echo "   - data/output/pipeline_report_*.json (実行レポート)"
    echo ""
    echo "📊 統計確認: cat data/output/bungo_stats_*.json | python -m json.tool"
else
    echo ""
    echo "❌ パイプライン実行に失敗しました"
    echo "📋 詳細は実行ログを確認してください: full_pipeline_*.log"
    exit 1
fi 