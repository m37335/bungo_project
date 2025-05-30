#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細住所抽出機能のテストスクリプト
Google Maps連携機能のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bungo_collector import BungoCollector

def test_detailed_places():
    """詳細住所抽出機能をテスト"""
    print("=== 詳細住所抽出機能テスト ===")
    
    collector = BungoCollector()
    
    # テスト用作家データ
    test_authors = ["夏目漱石", "太宰治", "宮沢賢治"]
    
    print(f"テスト対象作家: {', '.join(test_authors)}")
    
    for author in test_authors:
        print(f"\n--- {author} のテスト ---")
        
        # Wikipedia本文取得
        content = collector.get_wikipedia_content(author)
        if not content:
            print(f"❌ {author}: Wikipedia本文取得失敗")
            continue
        
        # 詳細地名抽出
        extracted_data = collector.extract_works_and_places(author, content)
        
        print(f"✅ 作品数: {len(extracted_data['works'])}")
        print(f"   作品: {extracted_data['works'][:3]}...")
        
        print(f"✅ 従来地名数: {len(extracted_data['places'])}")
        print(f"   地名: {extracted_data['places']}")
        
        print(f"✅ 詳細地名数: {len(extracted_data.get('detailed_places', []))}")
        
        # 詳細地名の内容確認
        detailed_places = extracted_data.get('detailed_places', [])
        for i, place_info in enumerate(detailed_places[:5]):  # 最大5件表示
            maps_ready = "○" if collector._is_maps_ready(place_info['name']) else "要確認"
            print(f"   {i+1}. {place_info['name']} ({place_info['type']}) - Maps準備: {maps_ready}")
            if place_info.get('context'):
                print(f"      文脈: {place_info['context'][:80]}...")
        
        # Google Maps検索クエリテスト
        if detailed_places:
            sample_place = detailed_places[0]
            query = collector._create_maps_query(author, sample_place)
            url = collector._create_maps_url(sample_place['name'])
            print(f"   サンプル検索クエリ: {query}")
            print(f"   サンプルMaps URL: {url}")

def test_google_maps_export():
    """Google Maps用エクスポート機能をテスト"""
    print("\n=== Google Maps用エクスポート機能テスト ===")
    
    collector = BungoCollector()
    
    # 簡単なテストデータを作成
    test_data = {
        'name': '夏目漱石',
        'works': ['吾輩は猫である', 'こころ', '坊っちゃん'],
        'places': ['東京', '愛媛'],
        'detailed_places': [
            {
                'name': '夏目漱石記念館',
                'type': '記念館・文学施設',
                'context': '東京都新宿区早稲田南町にある文学館'
            },
            {
                'name': '松山市',
                'type': '居住地',
                'context': '教師として赴任し坊っちゃんを執筆'
            },
            {
                'name': '雑司ヶ谷霊園',
                'type': '墓所',
                'context': '東京都豊島区にある霊園に眠る'
            }
        ]
    }
    
    collector.authors_data = [test_data]
    
    # Google Maps用エクスポート実行
    maps_df = collector.export_for_googlemaps("test_googlemaps.csv")
    
    if not maps_df.empty:
        print(f"✅ Google Maps用データ生成成功: {len(maps_df)}行")
        print("\n生成されたデータ:")
        for _, row in maps_df.iterrows():
            print(f"  - {row['地名']} ({row['種類']}) - {row['準備状況']}")
            print(f"    検索クエリ: {row['検索クエリ']}")
    else:
        print("❌ Google Maps用データ生成失敗")
    
    # 統計情報テスト
    stats = collector.generate_maps_summary()
    print(f"\n統計情報:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

def test_normalization():
    """地名正規化機能をテスト"""
    print("\n=== 地名正規化機能テスト ===")
    
    collector = BungoCollector()
    
    test_places = [
        "東京",
        "夏目漱石記念館",
        "松山市",
        "千代田区",
        "早稲田南町7-1",
        "青森"
    ]
    
    print("地名正規化テスト:")
    for place in test_places:
        normalized = collector._normalize_place_name(place)
        is_ready = collector._is_maps_ready(place)
        status = "○" if is_ready else "要確認"
        print(f"  {place} → {normalized} ({status})")

if __name__ == "__main__":
    print("🗺️ 詳細住所抽出＆Google Maps連携機能テスト")
    print("=" * 50)
    
    # 各テストを実行
    test_detailed_places()
    test_google_maps_export() 
    test_normalization()
    
    print("\n🎉 全テスト完了！") 