#!/usr/bin/env python3
"""
BungoCollector Google Sheets機能テスト

実際のBungoCollectorを使ってGoogle Sheetsにデータを出力するテスト
"""

from bungo_collector import BungoCollector
import pandas as pd

def main():
    print("📊 BungoCollector Google Sheets機能テスト")
    print("="*50)
    
    # テスト用データフレーム作成
    test_data = [
        ['夏目漱石', '坊っちゃん', '東京'],
        ['夏目漱石', 'こころ', '東京'],
        ['芥川龍之介', '羅生門', '東京'],
        ['太宰治', '人間失格', '青森'],
        ['宮沢賢治', '銀河鉄道の夜', '岩手']
    ]
    
    df = pd.DataFrame(test_data, columns=['作家名', '作品名', '所縁の土地'])
    
    print("📋 テスト用データ:")
    print(df.to_string(index=False))
    print()
    
    # BungoCollectorでGoogle Sheets出力
    try:
        collector = BungoCollector()
        print("📤 Google Sheetsに出力中...")
        
        collector.save_to_google_sheets(df, '文豪テストデータ')
        
        print("✅ Google Sheets出力テスト成功！")
        print()
        print("🎯 これで日本文豪プロジェクトでGoogle Sheets出力が利用可能です。")
        print("📄 'process_all_authors()' を実行して本格的なデータ収集・出力ができます。")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("🔧 credentials.jsonの設定を再確認してください。")

if __name__ == "__main__":
    main() 