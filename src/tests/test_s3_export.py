#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S3機能完了確認テスト（ジオコード・GeoJSONエクスポート）
仕様書 S3: 70%以上緯度経度取得、MapKit描画対応
"""

import json
import logging
from pathlib import Path

from db_utils import BungoDatabase
from export_geojson import GeoJSONExporter

# ログ設定
logging.basicConfig(level=logging.INFO)

def test_s3_completion():
    """S3機能の完了確認テスト"""
    print("🎯 S3機能完了確認テスト開始")
    print("目標: 70%以上ジオコーディング成功率 + MapKit対応GeoJSON")
    
    # 先ほどのGiNZAテストデータベースを使用
    db_path = "test_ginza.db"
    if not Path(db_path).exists():
        print(f"❌ テストデータベースが見つかりません: {db_path}")
        print("先にtest_ginza_pipeline.pyを実行してください")
        return False
    
    db = BungoDatabase(db_type="sqlite", db_path=db_path)
    exporter = GeoJSONExporter("output")
    
    try:
        # 1. データベース統計確認
        print("\n📊 データベース統計:")
        stats = db.get_stats()
        print(f"   作者数: {stats.get('authors', 0)}")
        print(f"   作品数: {stats.get('works', 0)}")
        print(f"   地名数: {stats.get('places', 0)}")
        
        # 2. ジオコーディング統計確認
        df = exporter._get_places_dataframe(db)
        
        if df.empty:
            print("❌ ジオコーディング済み地名データがありません")
            return False
        
        total_places = len(df)
        geocoded_places = len(df[df['latitude'].notna() & df['longitude'].notna()])
        geocoding_rate = geocoded_places / total_places * 100 if total_places > 0 else 0
        
        print(f"\n🗺️ ジオコーディング結果:")
        print(f"   総地名数: {total_places}")
        print(f"   ジオコーディング済み: {geocoded_places}")
        print(f"   成功率: {geocoding_rate:.1f}%")
        
        # S3成功基準判定
        target_rate = 70.0
        geocoding_success = geocoding_rate >= target_rate
        
        if geocoding_success:
            print(f"✅ ジオコーディング成功率 {geocoding_rate:.1f}% ≥ 目標{target_rate}%")
        else:
            print(f"❌ ジオコーディング成功率 {geocoding_rate:.1f}% < 目標{target_rate}%")
        
        # 3. GeoJSONエクスポート
        print(f"\n📤 GeoJSONエクスポート実行:")
        geojson_path = exporter.export_from_database(db, "bungo_places_s3.geojson")
        
        if not geojson_path or not Path(geojson_path).exists():
            print("❌ GeoJSONエクスポート失敗")
            return False
        
        # 4. GeoJSONファイル検証
        print(f"\n🔍 GeoJSONファイル検証: {geojson_path}")
        
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # 基本構造チェック
        required_fields = ['type', 'features', 'metadata']
        structure_valid = all(field in geojson_data for field in required_fields)
        
        if structure_valid:
            print("✅ GeoJSON基本構造: 正常")
        else:
            print("❌ GeoJSON基本構造: 異常")
            return False
        
        # Feature構造チェック
        features = geojson_data.get('features', [])
        print(f"   Features数: {len(features)}")
        
        if features:
            sample_feature = features[0]
            mapkit_properties = ['title', 'subtitle', 'description', 'context']
            mapkit_valid = all(prop in sample_feature.get('properties', {}) for prop in mapkit_properties)
            
            if mapkit_valid:
                print("✅ MapKit対応プロパティ: 完備")
            else:
                print("❌ MapKit対応プロパティ: 不足")
                missing = [p for p in mapkit_properties if p not in sample_feature.get('properties', {})]
                print(f"    不足プロパティ: {missing}")
                return False
        
        # 5. 統計情報エクスポート
        print(f"\n📈 統計情報エクスポート:")
        stats_path = exporter.export_summary_stats(db, "bungo_stats_s3.json")
        csv_path = exporter.export_csv_for_analysis(db, "bungo_analysis_s3.csv")
        
        # 6. 地名分布確認
        print(f"\n🏛️ 地名分布:")
        place_counts = df['place_name'].value_counts().head(10)
        for place, count in place_counts.items():
            print(f"   {place}: {count}件")
        
        # 7. 作者別統計
        print(f"\n👨‍💼 作者別統計:")
        author_counts = df['author_name'].value_counts()
        for author, count in author_counts.items():
            print(f"   {author}: {count}件")
        
        # 8. 抽出方法別統計
        print(f"\n🤖 抽出方法別統計:")
        method_counts = df['extraction_method'].value_counts()
        for method, count in method_counts.items():
            print(f"   {method}: {count}件")
        
        # 9. サンプル地名表示
        print(f"\n📍 サンプル地名（MapKit表示用）:")
        for i, (_, row) in enumerate(df.head(5).iterrows()):
            print(f"   {i+1}. {row['place_name']}")
            print(f"      座標: {row['latitude']:.4f}, {row['longitude']:.4f}")
            print(f"      作品: {row['author_name']}『{row['work_title']}』")
            if row.get('address'):
                print(f"      住所: {row['address']}")
            print()
        
        # S3完了判定
        s3_complete = geocoding_success and structure_valid and mapkit_valid and len(features) > 0
        
        print(f"\n🎯 S3機能完了確認結果:")
        print(f"   ジオコーディング: {'✅' if geocoding_success else '❌'} ({geocoding_rate:.1f}%)")
        print(f"   GeoJSON生成: {'✅' if len(features) > 0 else '❌'} ({len(features)}件)")
        print(f"   MapKit対応: {'✅' if mapkit_valid else '❌'}")
        print(f"   S3機能完了: {'✅ 成功' if s3_complete else '❌ 未完了'}")
        
        if s3_complete:
            print(f"\n🎉 S3機能が正常に完了しました！")
            print(f"   出力ファイル:")
            print(f"     - GeoJSON: {geojson_path}")
            print(f"     - 統計情報: {stats_path}")
            print(f"     - 分析CSV: {csv_path}")
        
        return s3_complete
        
    except Exception as e:
        print(f"❌ S3テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_s3_completion()
    exit(0 if success else 1) 