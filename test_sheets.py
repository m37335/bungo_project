#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets保存機能テスト
"""

from bungo_collector import BungoCollector
import pandas as pd

def test_sheets_save():
    """Google Sheets保存機能のテスト"""
    print("=== Google Sheets保存機能テスト ===")
    
    # 小さなサンプルデータを作成
    test_data = {
        '作家名': ['夏目漱石', '太宰治', '宮沢賢治'],
        '作品名': ['吾輩は猫である', '人間失格', '銀河鉄道の夜'],
        '所縁の地': ['東京都新宿区', '青森県五所川原市', '岩手県花巻市'],
        'Google Maps準備済み': ['○', '○', '○']
    }
    test_df = pd.DataFrame(test_data)
    
    print('テストデータ:')
    print(test_df)
    print()
    
    # BungoCollectorインスタンス作成
    collector = BungoCollector()
    
    # 効率的な保存方法でテスト
    print('効率的Google Sheets保存をテスト中...')
    result = collector.save_to_google_sheets_efficient(test_df, 'テスト用文豪データ_効率版')
    
    if result:
        print(f'✅ 成功！URL: {result}')
        return True
    else:
        print('❌ 保存失敗')
        return False

def test_existing_data_save():
    """既存のCSVデータをGoogle Sheetsに保存"""
    print("\n=== 既存データのGoogle Sheets保存 ===")
    
    collector = BungoCollector()
    
    # 既存のCSVファイルがあるかチェック
    try:
        df = pd.read_csv('authors_googlemaps.csv')
        print(f"GoogleMaps用データ発見: {len(df)}行")
        
        # データサイズに応じて保存方法を選択
        if len(df) <= 100:
            print("小さなデータなので効率的保存を使用")
            result = collector.save_to_google_sheets_efficient(df, '文豪GoogleMapsデータ_効率版')
        else:
            print("大きなデータなので通常保存を使用（改良版）")
            result = collector.save_to_google_sheets(df, '文豪GoogleMapsデータ_改良版')
        
        if result:
            print(f'✅ GoogleMaps用データ保存成功: {result}')
        
    except FileNotFoundError:
        print("❌ authors_googlemaps.csv が見つかりません")
    
    # 標準データも試す
    try:
        df_detailed = pd.read_csv('authors_detailed.csv')
        print(f"詳細データ発見: {len(df_detailed)}行")
        
        # データサイズに応じて保存方法を選択
        if len(df_detailed) <= 100:
            print("小さなデータなので効率的保存を使用")
            result = collector.save_to_google_sheets_efficient(df_detailed, '文豪詳細データ_効率版')
        else:
            print("大きなデータなので通常保存を使用（改良版）")
            result = collector.save_to_google_sheets(df_detailed, '文豪詳細データ_改良版')
        
        if result:
            print(f'✅ 詳細データ保存成功: {result}')
        
    except FileNotFoundError:
        print("❌ authors_detailed.csv が見つかりません")

if __name__ == "__main__":
    # テスト実行
    success = test_sheets_save()
    
    if success:
        print("\n基本テスト成功！既存データも保存してみます...")
        test_existing_data_save()
    else:
        print("\n基本テストが失敗しました。設定を確認してください。")
        print("- credentials.json が存在するか")
        print("- Google Sheets APIが有効になっているか")
        print("- 必要なライブラリがインストールされているか") 