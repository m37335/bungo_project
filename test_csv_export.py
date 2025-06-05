#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV エクスポート機能テスト
"""

import os
import csv
from pathlib import Path
from export_csv import CSVExporter, export_db_to_csv

def test_csv_export():
    """CSVエクスポート機能のテスト"""
    print("🧪 CSVエクスポート機能テスト開始")
    print("=" * 50)
    
    # データベースパス確認
    db_path = "test_ginza.db"
    if not Path(db_path).exists():
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    # エクスポーター初期化
    exporter = CSVExporter(db_path, "output")
    
    # 統計情報表示
    stats = exporter.get_export_stats()
    print(f"📊 データベース統計:")
    print(f"   作者: {stats['authors_count']}名")
    print(f"   作品: {stats['works_count']}件")
    print(f"   地名: {stats['places_count']}箇所")
    print(f"   ジオコーディング済み: {stats['geocoded_places_count']}箇所 ({stats['geocoding_rate']:.1f}%)")
    print()
    
    # 各種エクスポートテスト
    tests = [
        ("作者データ", lambda: exporter.export_authors("test_authors.csv")),
        ("作品データ", lambda: exporter.export_works("test_works.csv")),
        ("地名データ", lambda: exporter.export_places("test_places.csv")),
        ("地名データ（ジオコーディング済み）", lambda: exporter.export_places("test_places_geocoded.csv", geocoded_only=True)),
        ("結合データ", lambda: exporter.export_combined_data("test_combined.csv")),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"🔍 {test_name}テスト:")
        try:
            filepath = test_func()
            
            # ファイル存在確認
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"   ✅ エクスポート成功: {filepath} ({file_size} bytes)")
                
                # CSV内容確認（最初の数行）
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        print(f"   📋 列数: {len(header)}")
                        
                        # データ行数カウント
                        row_count = sum(1 for _ in reader)
                        print(f"   📊 データ行数: {row_count}")
                        
                        # 日本語文字確認
                        f.seek(0)
                        content = f.read(200)  # 最初の200文字
                        has_japanese = any(ord(c) > 127 for c in content)
                        print(f"   🗾 日本語文字: {'あり' if has_japanese else 'なし'}")
                        
                except Exception as e:
                    print(f"   ⚠️ CSV内容確認エラー: {e}")
                
                results.append(True)
            else:
                print(f"   ❌ ファイルが作成されませんでした")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            results.append(False)
        
        print()
    
    # 総合結果
    success_count = sum(results)
    total_count = len(results)
    overall_success = success_count == total_count
    
    print("=" * 50)
    print(f"🎯 CSVエクスポートテスト結果:")
    print(f"   成功: {success_count}/{total_count}")
    print(f"   {'✅ 全テスト合格' if overall_success else '❌ 一部テスト失敗'}")
    
    return overall_success

def test_api_integration():
    """API統合テスト（便利関数）"""
    print("\n🌐 API統合テスト:")
    
    try:
        # 便利関数テスト
        results = export_db_to_csv(
            db_path="test_ginza.db",
            output_dir="output",
            export_type="combined",
            author_filter="夏目漱石"
        )
        
        print(f"   ✅ 便利関数テスト成功")
        for key, filepath in results.items():
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"      {key}: {os.path.basename(filepath)} ({file_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 便利関数テストエラー: {e}")
        return False

def show_csv_usage():
    """CSV機能の使用方法表示"""
    print("\n💡 CSVエクスポート機能の使い方:")
    print("1. コマンドライン:")
    print("   python export_csv.py --type all")
    print("   python export_csv.py --type places --geocoded-only")
    print("   python export_csv.py --type combined --author 夏目漱石")
    
    print("\n2. Python コード:")
    print("   from export_csv import CSVExporter")
    print("   exporter = CSVExporter('test_ginza.db', 'output')")
    print("   exporter.export_all()")
    
    print("\n3. API エンドポイント:")
    print("   GET /export/csv?export_type=all")
    print("   GET /export/csv?export_type=places&geocoded_only=true")
    print("   GET /export/csv/download/{filename}")

def main():
    """メインテスト実行"""
    success1 = test_csv_export()
    success2 = test_api_integration()
    
    if success1 and success2:
        print("\n🎉 CSVエクスポート機能が正常に動作しています！")
        show_csv_usage()
    else:
        print("\n❌ 一部機能に問題があります。ログを確認してください。")

if __name__ == "__main__":
    main() 