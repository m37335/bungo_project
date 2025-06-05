#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪地図システム メインCLI
仕様書 bungo_update_spec_draft01.md 6章CLI仕様に基づく実装
"""

import argparse
import logging
import sys
import os
from typing import Optional
from datetime import datetime

# ローカルモジュールインポート
try:
    from db_utils import BungoDatabase
    from geocode_utils import GeocodeUtils
    from export_geojson import GeoJSONExporter
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    print("必要なモジュールをインストールしてください: pip install -r requirements.txt")
    sys.exit(1)


def setup_logging(verbose: bool = False):
    """ログ設定"""
    level = logging.DEBUG if verbose else logging.INFO
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'bungo_cli_{timestamp}.log')
        ]
    )


def cmd_geocode(args):
    """ジオコーディングコマンド"""
    print("🗺️ S3: ジオコーディング処理を開始します...")
    
    # データベース接続
    db = BungoDatabase(args.db_type, args.db_path)
    
    # ジオコーダー初期化
    geocoder = GeocodeUtils(google_api_key=args.google_api_key)
    
    try:
        # データベース内の地名をジオコーディング
        stats = geocoder.update_database_places(db, batch_size=args.batch_size)
        
        print(f"✅ ジオコーディング完了")
        print(f"   処理対象: {stats['total']}件")
        print(f"   更新成功: {stats['updated']}件")
        print(f"   成功率: {stats['success_rate']:.1f}%")
        
        # S3完了基準チェック（70%以上）
        if stats['success_rate'] >= 70.0:
            print("🎉 S3完了基準達成: ジオコーディング成功率 ≥ 70%")
        else:
            print(f"⚠️ S3完了基準未達: ジオコーディング成功率 {stats['success_rate']:.1f}% < 70%")
    
    except Exception as e:
        print(f"❌ ジオコーディングエラー: {e}")
        return 1
    
    finally:
        db.close()
    
    return 0


def cmd_export_geojson(args):
    """GeoJSONエクスポートコマンド"""
    print("📤 S3: GeoJSONエクスポート処理を開始します...")
    
    # データベース接続
    db = BungoDatabase(args.db_type, args.db_path)
    
    # エクスポーター初期化
    exporter = GeoJSONExporter(args.output_dir)
    
    try:
        # GeoJSONエクスポート
        geojson_path = exporter.export_from_database(db, args.output_filename)
        
        if geojson_path:
            print(f"✅ GeoJSONエクスポート完了: {geojson_path}")
        else:
            print("⚠️ エクスポート可能なデータがありませんでした")
            return 1
        
        # 統計情報出力（オプション）
        if args.include_stats:
            stats_path = exporter.export_summary_stats(db)
            print(f"📊 統計情報出力: {stats_path}")
        
        # 分析用CSV出力（オプション）
        if args.include_csv:
            csv_path = exporter.export_csv_for_analysis(db)
            print(f"📋 分析用CSV出力: {csv_path}")
        
        print("🎉 S3: GeoJSONエクスポート機能完了")
    
    except Exception as e:
        print(f"❌ エクスポートエラー: {e}")
        return 1
    
    finally:
        db.close()
    
    return 0


def cmd_s3_complete(args):
    """S3完了確認コマンド"""
    print("🎯 S3: ジオコーディング＆エクスポート統合処理を開始します...")
    
    # ジオコーディング実行
    print("\n== Step 1: ジオコーディング ==")
    geocode_result = cmd_geocode(args)
    
    if geocode_result != 0:
        print("❌ ジオコーディング処理でエラーが発生しました")
        return 1
    
    # GeoJSONエクスポート実行
    print("\n== Step 2: GeoJSONエクスポート ==")
    export_result = cmd_export_geojson(args)
    
    if export_result != 0:
        print("❌ エクスポート処理でエラーが発生しました")
        return 1
    
    # S3完了基準の最終チェック
    print("\n== S3完了基準チェック ==")
    db = BungoDatabase(args.db_type, args.db_path)
    
    try:
        stats = db.get_stats()
        geocoded_rate = stats.get('geocoded_rate', 0)
        
        print(f"📊 最終統計:")
        print(f"   作者数: {stats.get('authors_count', 0)}")
        print(f"   作品数: {stats.get('works_count', 0)}")
        print(f"   地名数: {stats.get('places_count', 0)}")
        print(f"   ジオコーディング率: {geocoded_rate:.1f}%")
        
        if geocoded_rate >= 70.0:
            print("🎉 S3完了: ジオコーディング＆エクスポート機能完成")
            print("   ✅ 70%以上の緯度経度取得達成")
            print("   ✅ MapKit用GeoJSON出力完了")
            return 0
        else:
            print(f"⚠️ S3未完了: ジオコーディング率 {geocoded_rate:.1f}% < 70%")
            return 1
    
    finally:
        db.close()


def cmd_search(args):
    """検索コマンド（既存機能の呼び出し）"""
    print("🔍 検索機能は bungo_search_cli.py を使用してください")
    print("例: python bungo_search_cli.py author '夏目'")
    return 0


def main():
    """メインCLI関数"""
    parser = argparse.ArgumentParser(
        description='文豪ゆかり地図システム - S3: ジオコーディング・エクスポート機能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # S3統合処理（ジオコーディング→エクスポート）
  python bungo_cli.py s3 --db-path bungo_production.db

  # ジオコーディングのみ実行
  python bungo_cli.py geocode --db-path bungo_production.db

  # GeoJSONエクスポートのみ実行
  python bungo_cli.py export --db-path bungo_production.db --include-stats

環境変数:
  GOOGLE_MAPS_API_KEY: Google Maps APIキー（ジオコーディング精度向上）
        """
    )
    
    # 共通オプション
    parser.add_argument('--db-type', choices=['sqlite', 'sheets'], default='sqlite',
                       help='データベース種別 (デフォルト: sqlite)')
    parser.add_argument('--db-path', default='bungo_production.db',
                       help='データベースパス/SpreadsheetID (デフォルト: bungo_production.db)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細ログ出力')
    
    # サブコマンド
    subparsers = parser.add_subparsers(dest='command', help='コマンド')
    
    # S3統合コマンド
    s3_parser = subparsers.add_parser('s3', help='S3: ジオコーディング＆エクスポート統合処理')
    s3_parser.add_argument('--google-api-key', help='Google Maps APIキー')
    s3_parser.add_argument('--batch-size', type=int, default=50, help='ジオコーディングバッチサイズ')
    s3_parser.add_argument('--output-dir', default='output', help='出力ディレクトリ')
    s3_parser.add_argument('--output-filename', default='bungo_places.geojson', help='GeoJSONファイル名')
    s3_parser.add_argument('--include-stats', action='store_true', help='統計情報も出力')
    s3_parser.add_argument('--include-csv', action='store_true', help='分析用CSVも出力')
    s3_parser.set_defaults(func=cmd_s3_complete)
    
    # ジオコーディングコマンド
    geocode_parser = subparsers.add_parser('geocode', help='ジオコーディング処理')
    geocode_parser.add_argument('--google-api-key', help='Google Maps APIキー')
    geocode_parser.add_argument('--batch-size', type=int, default=50, help='バッチサイズ')
    geocode_parser.set_defaults(func=cmd_geocode)
    
    # エクスポートコマンド
    export_parser = subparsers.add_parser('export', help='GeoJSONエクスポート')
    export_parser.add_argument('--output-dir', default='output', help='出力ディレクトリ')
    export_parser.add_argument('--output-filename', default='bungo_places.geojson', help='出力ファイル名')
    export_parser.add_argument('--include-stats', action='store_true', help='統計情報も出力')
    export_parser.add_argument('--include-csv', action='store_true', help='分析用CSVも出力')
    export_parser.set_defaults(func=cmd_export_geojson)
    
    # 検索コマンド（既存への誘導）
    search_parser = subparsers.add_parser('search', help='検索機能（既存CLIを使用）')
    search_parser.set_defaults(func=cmd_search)
    
    # 引数解析
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # ログ設定
    setup_logging(args.verbose)
    
    # コマンド実行
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n⚠️ 処理がユーザーによって中断されました")
        return 130
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 