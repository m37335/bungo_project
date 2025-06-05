#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草枕地名抽出テスト
"""

from aozora_utils import AozoraUtils
from aozora_place_extract import AozoraPlaceExtractor
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)

def test_kusamakura():
    aozora = AozoraUtils()
    extractor = AozoraPlaceExtractor()

    # 草枕の作品情報を取得
    works = aozora.search_works_in_catalog('夏目漱石')
    kusamakura = [w for w in works if '草枕' in w['title']]
    
    if not kusamakura:
        print("草枕が見つかりません")
        return
    
    work = kusamakura[0]
    print(f"作品: {work['title']}")
    
    # テキストダウンロード
    text = aozora.download_text(work)
    if not text:
        print("テキストダウンロード失敗")
        return
        
    print(f"テキスト長: {len(text)}文字")
    print(f"先頭部分: {text[:300]}...")
    
    # 地名抽出
    work_info = {'author_name': work['author_name'], 'title': work['title']}
    places = extractor.extract_places_from_text(text, work_info)
    
    print(f"\n🗺️ 地名抽出結果: {len(places)}件")
    for i, place in enumerate(places[:10]):
        print(f"  {i+1}. {place['place_name']} ({place['extraction_method']})")
        if 'context' in place and place['context']:
            print(f"     コンテキスト: {place['context'][:100]}...")
        print()

if __name__ == "__main__":
    test_kusamakura() 