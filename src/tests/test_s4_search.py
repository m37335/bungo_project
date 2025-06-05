#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S4機能完了確認テスト（検索機能）
仕様書 S4: 作者名・作品名・地名で 0.5 秒以内に検索ヒット
"""

import time
import logging
from pathlib import Path

from db_utils import BungoDatabase

# ログ設定
logging.basicConfig(level=logging.INFO)

def test_s4_completion():
    """S4機能の完了確認テスト"""
    print("🎯 S4機能完了確認テスト開始")
    print("目標: 作者・作品・地名検索 ≤0.5秒以内")
    
    # テストデータベース確認
    db_path = "test_ginza.db"
    if not Path(db_path).exists():
        print(f"❌ テストデータベースが見つかりません: {db_path}")
        print("先にtest_ginza_pipeline.pyを実行してください")
        return False
    
    db = BungoDatabase(db_type="sqlite", db_path=db_path)
    
    try:
        print("\n📊 データベース統計:")
        stats = db.get_stats()
        total_authors = stats.get('authors_count', 0)
        total_works = stats.get('works_count', 0) 
        total_places = stats.get('places_count', 0)
        print(f"   作者数: {total_authors}")
        print(f"   作品数: {total_works}")
        print(f"   地名数: {total_places}")
        
        if total_authors == 0 or total_works == 0 or total_places == 0:
            print("❌ テストデータが不足しています")
            return False
        
        # S4検索テストケース
        test_cases = [
            # (検索タイプ, クエリ, 説明)
            ("author", "夏目", "作者名検索"),
            ("author", "漱石", "作者名部分検索"),
            ("work", "草枕", "作品名検索"),
            ("work", "草", "作品名部分検索"),
            ("place", "東京", "地名検索"),
            ("place", "京都", "地名検索2"),
            ("place", "鎌倉", "地名検索3"),
        ]
        
        print(f"\n🔍 検索性能テスト:")
        all_fast = True
        target_time = 0.5  # 目標0.5秒
        
        for search_type, query, description in test_cases:
            print(f"\n   テスト: {description} 「{query}」")
            
            # 検索実行・計測
            start_time = time.time()
            
            if search_type == "author":
                results = db.search_authors(query)
            elif search_type == "work":
                results = db.search_works(query)
            elif search_type == "place":
                results = db.search_places(query)
            
            elapsed_time = time.time() - start_time
            
            # 結果表示
            print(f"      実行時間: {elapsed_time:.3f}秒")
            print(f"      結果件数: {len(results)}件")
            
            if elapsed_time <= target_time:
                print(f"      ✅ 性能OK ({elapsed_time:.3f}s ≤ {target_time}s)")
            else:
                print(f"      ❌ 性能NG ({elapsed_time:.3f}s > {target_time}s)")
                all_fast = False
            
            # サンプル結果表示
            if results:
                sample = results[0]
                if search_type == "author":
                    print(f"      サンプル: {sample.get('name', 'N/A')}")
                elif search_type == "work":
                    print(f"      サンプル: {sample.get('author_name', 'N/A')} - {sample.get('title', 'N/A')}")
                elif search_type == "place":
                    print(f"      サンプル: {sample.get('place_name', 'N/A')} in {sample.get('work_title', 'N/A')}")
        
        # 検索機能テスト
        print(f"\n🎯 検索機能テスト:")
        
        # 1. 作者検索 → 作品一覧
        print(f"   1. 作者検索 → 作品一覧:")
        authors = db.search_authors("夏目")
        if authors:
            author_name = authors[0]['name']
            print(f"      検索作者: {author_name}")
            
            works = db.search_works("")  # 全作品取得
            author_works = [w for w in works if w.get('author_name') == author_name]
            print(f"      作品数: {len(author_works)}件")
            
            for work in author_works[:3]:
                print(f"        - {work.get('title', 'N/A')}")
        
        # 2. 作品検索 → 地名一覧
        print(f"\n   2. 作品検索 → 地名一覧:")
        works = db.search_works("草枕")
        if works:
            work_title = works[0]['title']
            print(f"      検索作品: {work_title}")
            
            places = db.search_places("")  # 全地名取得
            work_places = [p for p in places if p.get('work_title') == work_title]
            print(f"      地名数: {len(work_places)}件")
            
            for place in work_places[:5]:
                print(f"        - {place.get('place_name', 'N/A')} ({place.get('latitude', 'N/A')}, {place.get('longitude', 'N/A')})")
        
        # 3. 地名検索 → 作者・作品逆引き
        print(f"\n   3. 地名検索 → 作者・作品逆引き:")
        places = db.search_places("東京")
        if places:
            place_name = places[0]['place_name']
            print(f"      検索地名: {place_name}")
            
            # 該当する作者・作品の組み合わせ
            author_work_pairs = set()
            for place in places:
                if place.get('author_name') and place.get('work_title'):
                    author_work_pairs.add((place['author_name'], place['work_title']))
            
            print(f"      関連作品: {len(author_work_pairs)}件")
            for author, work in list(author_work_pairs)[:3]:
                print(f"        - {author}『{work}』")
        
        # 双方向検索テスト
        print(f"\n🔄 双方向検索テスト:")
        print(f"   作者→作品→地名→作者 の連鎖検索")
        
        # 作者 → 作品
        authors = db.search_authors("夏目")
        if authors:
            author = authors[0]
            print(f"   🧑 作者: {author['name']}")
            
            # 作品 → 地名
            works = [w for w in db.search_works("") if w.get('author_name') == author['name']]
            if works:
                work = works[0]
                print(f"   📚 作品: {work['title']}")
                
                # 地名 → 逆引き確認
                places = [p for p in db.search_places("") if p.get('work_title') == work['title']]
                if places:
                    place = places[0]
                    print(f"   🗺️ 地名: {place['place_name']}")
                    
                    # 逆引き検証
                    reverse_places = db.search_places(place['place_name'])
                    reverse_works = {p.get('work_title') for p in reverse_places}
                    reverse_authors = {p.get('author_name') for p in reverse_places}
                    
                    print(f"   ↩️ 逆引き結果:")
                    print(f"      関連作者: {', '.join(reverse_authors)}")
                    print(f"      関連作品: {', '.join(reverse_works)}")
                    
                    # 双方向性確認
                    bidirectional_ok = (
                        author['name'] in reverse_authors and 
                        work['title'] in reverse_works
                    )
                    print(f"   ✅ 双方向性: {'OK' if bidirectional_ok else 'NG'}")
        
        # S4完了判定
        functionality_ok = len(authors) > 0 and len(works) > 0 and len(places) > 0
        s4_complete = all_fast and functionality_ok
        
        print(f"\n🎯 S4機能完了確認結果:")
        print(f"   検索性能: {'✅' if all_fast else '❌'} (全検索 ≤{target_time}秒)")
        print(f"   検索機能: {'✅' if functionality_ok else '❌'} (作者・作品・地名)")
        print(f"   双方向検索: {'✅' if bidirectional_ok else '❌'}")
        print(f"   S4機能完了: {'✅ 成功' if s4_complete else '❌ 未完了'}")
        
        if s4_complete:
            print(f"\n🎉 S4機能が正常に完了しました！")
            print(f"   検索CLI: bungo_search_cli.py")
            print(f"   対話型検索: python bungo_search_cli.py --interactive")
            print(f"   統計表示: python bungo_search_cli.py --stats")
        
        return s4_complete
        
    except Exception as e:
        print(f"❌ S4テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_s4_completion()
    exit(0 if success else 1) 