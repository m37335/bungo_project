#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本格的なデータ移行実行スクリプト
bungo_enhanced_work_places.csv → bungo_production.db
"""

from migrate_legacy_data import migrate_legacy_csv_to_database
import os

if __name__ == "__main__":
    print("🚀 本格的なデータ移行開始")
    print("="*50)
    
    # 実際のデータ移行実行
    success = migrate_legacy_csv_to_database(
        csv_file="bungo_enhanced_work_places.csv",
        db_path="bungo_production.db"
    )
    
    if success:
        print("\n🎉 移行成功！")
        print("✅ データベース作成: bungo_production.db")
        print("💡 次のコマンドで検索可能:")
        print("   python bungo_search_cli.py --interactive")
        print("   python bungo_search_cli.py --stats")
        print("   python bungo_search_cli.py --place 東京")
    else:
        print("\n❌ 移行失敗")
        print("💡 CSVファイルとパスを確認してください") 