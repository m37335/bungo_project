#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪地図システム検索CLI
仕様書 bungo_update_spec_draft01.md 6章CLI仕様に基づく実装

使用例:
  bungo search author "夏目"      # 作者名あいまい検索 → 作品一覧
  bungo search work "坊っちゃん"   # 作品名検索 → 地名＋抜粋
  bungo search place "松山市"     # 地名検索 → 作者・作品逆引き
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

from db_utils import BungoDatabase


class BungoSearchEngine:
    """文豪地図システム検索エンジン"""
    
    def __init__(self, db_path: str = "test_ginza.db"):
        """
        Args:
            db_path: データベースファイルパス
        """
        if not Path(db_path).exists():
            raise FileNotFoundError(f"データベースファイルが見つかりません: {db_path}")
        
        self.db = BungoDatabase("sqlite", db_path)
        print(f"📚 データベース接続: {db_path}")
    
    def search_author(self, query: str, limit: int = 10) -> Dict:
        """
        作者名あいまい検索 → 作品一覧
        
        Args:
            query: 作者名検索クエリ
            limit: 最大結果数
            
        Returns:
            {
                'authors': [...],
                'works': [...],
                'execution_time': float
            }
        """
        start_time = time.time()
        
        # 作者検索
        authors = self.db.search_authors(query)[:limit]
        
        # 該当作者の作品一覧取得
        works = []
        for author in authors:
            author_works = self.db.search_works("")  # 全作品取得
            works.extend([w for w in author_works if w.get('author_name') == author['name']])
        
        execution_time = time.time() - start_time
        
        return {
            'authors': authors,
            'works': works[:limit],
            'execution_time': execution_time
        }
    
    def search_work(self, query: str, limit: int = 10) -> Dict:
        """
        作品名検索 → 地名＋抜粋
        
        Args:
            query: 作品名検索クエリ
            limit: 最大結果数
            
        Returns:
            {
                'works': [...],
                'places': [...],
                'execution_time': float
            }
        """
        start_time = time.time()
        
        # 作品検索
        works = self.db.search_works(query)[:limit]
        
        # 該当作品の地名一覧取得
        places = []
        for work in works:
            work_places = self.db.search_places("")  # 全地名取得
            places.extend([p for p in work_places if p.get('work_title') == work['title']])
        
        execution_time = time.time() - start_time
        
        return {
            'works': works,
            'places': places[:limit * 5],  # 地名は多めに表示
            'execution_time': execution_time
        }
    
    def search_place(self, query: str, limit: int = 10) -> Dict:
        """
        地名検索 → 作者・作品逆引き
        
        Args:
            query: 地名検索クエリ
            limit: 最大結果数
            
        Returns:
            {
                'places': [...],
                'authors': [...],
                'works': [...],
                'execution_time': float
            }
        """
        start_time = time.time()
        
        # 地名検索
        places = self.db.search_places(query)[:limit]
        
        # 関連作者・作品の逆引き
        authors = set()
        works = set()
        
        for place in places:
            if place.get('author_name'):
                authors.add(place['author_name'])
            if place.get('work_title'):
                works.add((place.get('author_name'), place['work_title']))
        
        execution_time = time.time() - start_time
        
        return {
            'places': places,
            'authors': list(authors),
            'works': [{'author_name': author, 'title': work} for author, work in works],
            'execution_time': execution_time
        }
    
    def get_statistics(self) -> Dict:
        """データベース統計取得"""
        return self.db.get_stats()
    
    def close(self):
        """データベース接続クローズ"""
        self.db.close()


def print_author_results(result: Dict, query: str):
    """作者検索結果表示"""
    authors = result['authors']
    works = result['works'] 
    exec_time = result['execution_time']
    
    print(f"\n🔍 作者検索「{query}」")
    print("=" * 50)
    print(f"⚡ 実行時間: {exec_time:.3f}秒")
    print(f"📊 結果: 作者{len(authors)}名、作品{len(works)}件")
    
    if not authors:
        print("❌ 該当する作者が見つかりません")
        return
    
    for i, author in enumerate(authors, 1):
        print(f"\n{i}. 👤 【作者】{author['name']}")
        if author.get('birth_year') or author.get('death_year'):
            birth = author.get('birth_year', '不明')
            death = author.get('death_year', '不明')
            print(f"   📅 生没年: {birth}-{death}")
        if author.get('wikipedia_url'):
            print(f"   🔗 Wikipedia: {author['wikipedia_url']}")
        
        # この作者の作品一覧
        author_works = [w for w in works if w.get('author_name') == author['name']]
        if author_works:
            print(f"   📚 作品一覧 ({len(author_works)}件):")
            for work in author_works[:5]:  # 最大5件
                print(f"      - {work['title']}")
                if work.get('aozora_url'):
                    print(f"        💻 青空文庫: {work['aozora_url']}")
        print()


def print_work_results(result: Dict, query: str):
    """作品検索結果表示"""
    works = result['works']
    places = result['places']
    exec_time = result['execution_time']
    
    print(f"\n🔍 作品検索「{query}」")
    print("=" * 50)
    print(f"⚡ 実行時間: {exec_time:.3f}秒")
    print(f"📊 結果: 作品{len(works)}件、地名{len(places)}箇所")
    
    if not works:
        print("❌ 該当する作品が見つかりません")
        return
    
    for i, work in enumerate(works, 1):
        print(f"\n{i}. 📚 【作品】{work.get('author_name', 'N/A')} - {work['title']}")
        if work.get('publication_year'):
            print(f"   📅 刊行年: {work['publication_year']}")
        if work.get('aozora_url'):
            print(f"   💻 青空文庫: {work['aozora_url']}")
        
        # この作品の地名一覧
        work_places = [p for p in places if p.get('work_title') == work['title']]
        if work_places:
            print(f"   🗺️ 登場地名 ({len(work_places)}箇所):")
            for place in work_places[:10]:  # 最大10箇所
                lat = place.get('latitude', 'N/A')
                lng = place.get('longitude', 'N/A')
                print(f"      📍 {place['place_name']} ({lat}, {lng})")
                if place.get('sentence'):
                    context = place['sentence'][:50] + "..." if len(place['sentence']) > 50 else place['sentence']
                    print(f"         💭 「{context}」")
        print()


def print_place_results(result: Dict, query: str):
    """地名検索結果表示"""
    places = result['places']
    authors = result['authors']
    works = result['works']
    exec_time = result['execution_time']
    
    print(f"\n🔍 地名検索「{query}」")
    print("=" * 50)
    print(f"⚡ 実行時間: {exec_time:.3f}秒")
    print(f"📊 結果: 地名{len(places)}箇所、関連作者{len(authors)}名、関連作品{len(works)}件")
    
    if not places:
        print("❌ 該当する地名が見つかりません")
        return
    
    # 地名詳細表示
    for i, place in enumerate(places, 1):
        print(f"\n{i}. 🗺️ 【地名】{place['place_name']}")
        print(f"   📚 作品: {place.get('author_name', 'N/A')} - {place.get('work_title', 'N/A')}")
        
        lat = place.get('latitude')
        lng = place.get('longitude')
        if lat and lng:
            print(f"   📍 座標: ({lat:.4f}, {lng:.4f})")
        if place.get('address'):
            print(f"   🏠 住所: {place['address']}")
        
        if place.get('sentence'):
            context = place['sentence'][:100] + "..." if len(place['sentence']) > 100 else place['sentence']
            print(f"   💭 文脈: 「{context}」")
    
    # 関連作者・作品サマリー
    if authors:
        print(f"\n👤 関連作者: {', '.join(authors)}")
    if works:
        print(f"📚 関連作品:")
        for work in works[:5]:
            print(f"   - {work['author_name']} 『{work['title']}』")


def main():
    """メインCLI関数"""
    parser = argparse.ArgumentParser(
        description='文豪地図システム検索CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python search.py author "夏目"        # 作者名あいまい検索
  python search.py work "坊っちゃん"     # 作品名検索
  python search.py place "松山市"       # 地名検索
  python search.py stats               # 統計表示

検索タイプ:
  author   作者名あいまい検索 → 作品一覧
  work     作品名検索 → 地名＋抜粋  
  place    地名検索 → 作者・作品逆引き
        """
    )
    
    # サブコマンド
    subparsers = parser.add_subparsers(dest='command', help='検索コマンド')
    
    # 作者検索
    author_parser = subparsers.add_parser('author', help='作者名あいまい検索')
    author_parser.add_argument('query', help='作者名（部分一致）')
    author_parser.add_argument('--limit', type=int, default=10, help='最大結果数')
    
    # 作品検索
    work_parser = subparsers.add_parser('work', help='作品名検索')
    work_parser.add_argument('query', help='作品名（部分一致）')
    work_parser.add_argument('--limit', type=int, default=10, help='最大結果数')
    
    # 地名検索
    place_parser = subparsers.add_parser('place', help='地名検索')
    place_parser.add_argument('query', help='地名（部分一致）')
    place_parser.add_argument('--limit', type=int, default=10, help='最大結果数')
    
    # 統計表示
    stats_parser = subparsers.add_parser('stats', help='データベース統計表示')
    
    # 共通オプション
    parser.add_argument('--db', default='test_ginza.db', help='データベースファイル')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細出力')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # 検索エンジン初期化
        search_engine = BungoSearchEngine(args.db)
        
        if args.command == 'author':
            result = search_engine.search_author(args.query, args.limit)
            print_author_results(result, args.query)
            
        elif args.command == 'work':
            result = search_engine.search_work(args.query, args.limit)
            print_work_results(result, args.query)
            
        elif args.command == 'place':
            result = search_engine.search_place(args.query, args.limit)
            print_place_results(result, args.query)
            
        elif args.command == 'stats':
            stats = search_engine.get_statistics()
            print("\n📈 データベース統計")
            print("=" * 30)
            print(f"👤 作者数: {stats.get('authors_count', 0)}名")
            print(f"📚 作品数: {stats.get('works_count', 0)}作品")
            print(f"🗺️ 地名数: {stats.get('places_count', 0)}箇所")
            print(f"📍 ジオコーディング率: {stats.get('geocoded_rate', 0):.1f}%")
            print(f"✅ ジオコーディング済み: {stats.get('geocoded_count', 0)}箇所")
        
        search_engine.close()
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 まずデータ収集を実行してください: python collect.py --test")
        return 1
    except Exception as e:
        print(f"❌ エラー: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 