#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GiNZA地名抽出パイプライン完全テスト
"""

import logging
import sys
from pathlib import Path

from db_utils import BungoDatabase
from aozora_utils import AozoraUtils
from aozora_place_extract import AozoraPlaceExtractor
from geocode_utils import GeocodeUtils

# ログ設定
logging.basicConfig(level=logging.INFO)

def test_ginza_pipeline():
    """GiNZAを使った完全パイプラインテスト"""
    print("🧪 GiNZA地名抽出パイプライン完全テスト開始")
    
    # 初期化
    db = BungoDatabase(db_type="sqlite", db_path="test_ginza.db")
    aozora = AozoraUtils()
    extractor = AozoraPlaceExtractor()
    geocoder = GeocodeUtils()
    
    try:
        # 1. 作者登録
        author_id = db.insert_author("夏目漱石")
        print(f"✅ 作者登録: 夏目漱石 (ID: {author_id})")
        
        # 2. 草枕のテキストを取得
        works = aozora.search_works_in_catalog('夏目漱石')
        kusamakura = [w for w in works if '草枕' in w['title']]
        
        if not kusamakura:
            print("❌ 草枕が見つかりません")
            return False
        
        work = kusamakura[0]
        text = aozora.download_text(work)
        
        if not text:
            print("❌ 草枕のテキスト取得失敗")
            return False
        
        print(f"✅ 草枕テキスト取得: {len(text)}文字")
        
        # 3. 作品登録
        work_id = db.insert_work(author_id, work['title'], aozora_url=work.get('text_url', ''))
        print(f"✅ 作品登録: {work['title']} (ID: {work_id})")
        
        # 4. 地名抽出
        work_info = {
            'author_name': '夏目漱石',
            'title': work['title'],
            'aozora_url': work.get('text_url', '')
        }
        
        places = extractor.extract_places_from_text(text, work_info)
        print(f"✅ 地名抽出: {len(places)}件")
        
        # 5. 地名登録
        place_count = 0
        for place in places:
            # コンテキストから前後文を分離
            context = place.get('context', '')
            before_text = context[:50] if len(context) > 50 else ''
            sentence = place.get('place_name', '')
            after_text = context[-50:] if len(context) > 50 else ''
            
            place_id = db.upsert_place(
                work_id=work_id,
                place_name=place['place_name'],
                before_text=before_text,
                sentence=sentence,
                after_text=after_text,
                extraction_method=place.get('extraction_method', 'ginza'),
                confidence=place.get('confidence', 0.8)
            )
            
            if place_id:
                place_count += 1
        
        print(f"✅ 地名登録: {place_count}件")
        
        # 6. ジオコーディング
        print("📍 ジオコーディング実行中...")
        geocode_stats = geocoder.update_database_places(db)
        geocoded_count = geocode_stats.get('updated', 0)
        print(f"✅ ジオコーディング: {geocoded_count}件")
        
        # 7. 結果確認
        print("\n📊 パイプライン結果:")
        print(f"   作者: 1名")
        print(f"   作品: 1作品")
        print(f"   地名: {place_count}件")
        print(f"   ジオコード: {geocoded_count}件")
        
        # サンプル地名表示
        print("\n🗺️ 抽出地名サンプル:")
        for i, place in enumerate(places[:10]):
            print(f"  {i+1}. {place['place_name']} ({place.get('extraction_method', '')})")
        
        return True
        
    except Exception as e:
        print(f"❌ パイプラインテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_ginza_pipeline()
    sys.exit(0 if success else 1) 