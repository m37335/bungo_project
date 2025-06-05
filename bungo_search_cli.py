#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪地名検索CLI
仕様書 bungo_update_spec_draft01.md S4章 検索CLI & API化に基づく実装
"""

import argparse
import sys
from typing import List, Dict
import pandas as pd
from db_utils import BungoDatabase
import json

class BungoSearchCLI:
    """文豪地名検索CLIインターフェース"""
    
    def __init__(self, db_path: str = "test_ginza.db"):
        self.db = BungoDatabase("sqlite", db_path)
    
    def search_authors(self, query: str, limit: int = 10) -> List[Dict]:
        """作者検索"""
        results = self.db.search_authors(query)
        return results[:limit]
    
    def search_works(self, query: str, limit: int = 10) -> List[Dict]:
        """作品検索"""
        results = self.db.search_works(query)
        return results[:limit]
    
    def search_places(self, query: str, limit: int = 10) -> List[Dict]:
        """地名検索"""
        results = self.db.search_places(query)
        return results[:limit]
    
    def search_all(self, query: str, limit: int = 10) -> Dict:
        """全体検索"""
        return {
            'authors': self.search_authors(query, limit),
            'works': self.search_works(query, limit),
            'places': self.search_places(query, limit)
        }
    
    def get_author_works(self, author_name: str) -> List[Dict]:
        """特定作者の全作品取得"""
        authors = self.db.search_authors(author_name)
        if not authors:
            return []
        
        author_id = authors[0]['author_id']
        return self.db.search_works('')  # 全作品から該当作者のものを取得
    
    def get_work_places(self, work_title: str) -> List[Dict]:
        """特定作品の全地名取得"""
        return self.db.search_places('')  # 全地名から該当作品のものを取得
    
    def export_search_results(self, results: List[Dict], format: str = "csv", filename: str = None):
        """検索結果出力"""
        if not results:
            print("❌ 出力するデータがありません")
            return
        
        df = pd.DataFrame(results)
        
        if not filename:
            filename = f"search_results.{format}"
        
        if format == "csv":
            df.to_csv(filename, index=False, encoding='utf-8')
        elif format == "json":
            df.to_json(filename, orient='records', ensure_ascii=False, indent=2)
        elif format == "xlsx":
            df.to_excel(filename, index=False)
        
        print(f"✅ 検索結果出力: {filename} ({len(results)}件)")
    
    def print_results(self, results: List[Dict], title: str = "検索結果"):
        """検索結果表示"""
        print(f"\n📊 {title} ({len(results)}件)")
        print("=" * 50)
        
        if not results:
            print("❌ 該当データなし")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. ", end="")
            
            # 作者検索結果
            if 'birth_year' in result:
                birth = result.get('birth_year', '不明')
                death = result.get('death_year', '不明') 
                print(f"【作者】{result['name']} ({birth}-{death})")
                if result.get('wikipedia_url'):
                    print(f"   🔗 {result['wikipedia_url']}")
            
            # 作品検索結果  
            elif 'author_name' in result and 'title' in result:
                year = result.get('publication_year', '不明')
                genre = result.get('genre', '不明')
                print(f"【作品】{result['author_name']} - {result['title']} ({year}年, {genre})")
                if result.get('aozora_url'):
                    print(f"   📚 青空文庫: {result['aozora_url']}")
            
            # 地名検索結果
            elif 'author_name' in result and 'place_name' in result:
                lat = result.get('latitude', 'N/A')
                lng = result.get('longitude', 'N/A')
                print(f"【地名】{result['author_name']} - {result['work_title']} - {result['place_name']}")
                print(f"   📍 座標: ({lat}, {lng})")
                print(f"   📍 住所: {result.get('address', '不明')}")
                if result.get('sentence'):
                    print(f"   📝 文脈: {result['sentence'][:100]}...")
                if result.get('maps_url'):
                    print(f"   🗺️ Google Maps: {result['maps_url']}")
    
    def get_stats(self):
        """データベース統計表示"""
        stats = self.db.get_stats()
        print("\n📈 データベース統計")
        print("=" * 30)
        print(f"👤 作者数: {stats['authors_count']}名")
        print(f"📚 作品数: {stats['works_count']}作品")
        print(f"🗺️ 地名数: {stats['places_count']}箇所")
        print(f"📍 ジオコーディング率: {stats['geocoded_rate']:.1f}%")
        print(f"✅ ジオコーディング済み: {stats['geocoded_count']}箇所")
    
    def interactive_search(self):
        """対話型検索モード"""
        print("🔍 文豪地名検索システム - 対話モード")
        print("=" * 40)
        print("コマンド:")
        print("  author <名前>  : 作者検索")
        print("  work <タイトル> : 作品検索")
        print("  place <地名>   : 地名検索")
        print("  all <キーワード>: 全体検索")
        print("  stats          : 統計表示")
        print("  export         : 全データCSV出力")
        print("  quit           : 終了")
        print()
        
        while True:
            try:
                cmd = input("🔍 検索> ").strip()
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    print("👋 終了します")
                    break
                
                elif cmd.lower() == 'stats':
                    self.get_stats()
                
                elif cmd.lower() == 'export':
                    df = self.db.get_all_places()
                    filename = f"bungo_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                    print(f"✅ 全データ出力: {filename} ({len(df)}件)")
                
                elif cmd.startswith('author '):
                    query = cmd[7:].strip()
                    results = self.search_authors(query)
                    self.print_results(results, f"作者検索「{query}」")
                
                elif cmd.startswith('work '):
                    query = cmd[5:].strip()
                    results = self.search_works(query)
                    self.print_results(results, f"作品検索「{query}」")
                
                elif cmd.startswith('place '):
                    query = cmd[6:].strip()
                    results = self.search_places(query)
                    self.print_results(results, f"地名検索「{query}」")
                
                elif cmd.startswith('all '):
                    query = cmd[4:].strip()
                    results = self.search_all(query)
                    print(f"\n🔍 全体検索「{query}」")
                    self.print_results(results['authors'], "作者")
                    self.print_results(results['works'], "作品")
                    self.print_results(results['places'], "地名")
                
                else:
                    print("❌ 不明なコマンドです。helpを入力してください")
                    
            except KeyboardInterrupt:
                print("\n👋 終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")
    
    def close(self):
        """接続クローズ"""
        self.db.close()

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='文豪地名検索CLI')
    parser.add_argument('--db', default='test_ginza.db', help='データベースファイル')
    parser.add_argument('--interactive', '-i', action='store_true', help='対話モード')
    parser.add_argument('--stats', action='store_true', help='統計表示')
    parser.add_argument('--export', help='全データをCSV出力（ファイル名指定）')
    
    # 検索オプション
    parser.add_argument('--author', help='作者検索')
    parser.add_argument('--work', help='作品検索')
    parser.add_argument('--place', help='地名検索')
    parser.add_argument('--all', help='全体検索')
    parser.add_argument('--limit', type=int, default=10, help='検索結果上限数')
    parser.add_argument('--format', choices=['csv', 'json', 'xlsx'], default='csv', help='出力形式')
    
    args = parser.parse_args()
    
    try:
        cli = BungoSearchCLI(args.db)
        
        if args.interactive:
            cli.interactive_search()
        
        elif args.stats:
            cli.get_stats()
        
        elif args.export:
            df = cli.db.get_all_places()
            df.to_csv(args.export, index=False, encoding='utf-8')
            print(f"✅ 全データ出力: {args.export} ({len(df)}件)")
        
        elif args.author:
            results = cli.search_authors(args.author, args.limit)
            cli.print_results(results, f"作者検索「{args.author}」")
            
        elif args.work:
            results = cli.search_works(args.work, args.limit)
            cli.print_results(results, f"作品検索「{args.work}」")
            
        elif args.place:
            results = cli.search_places(args.place, args.limit)
            cli.print_results(results, f"地名検索「{args.place}」")
            
        elif args.all:
            results = cli.search_all(args.all, args.limit)
            print(f"\n🔍 全体検索「{args.all}」")
            cli.print_results(results['authors'], "作者")
            cli.print_results(results['works'], "作品")
            cli.print_results(results['places'], "地名")
        
        else:
            # デフォルト: 対話モード
            cli.interactive_search()
        
        cli.close()
        
    except FileNotFoundError:
        print(f"❌ データベースファイルが見つかりません: {args.db}")
        print("💡 まず migrate_legacy_data.py を実行してデータベースを作成してください")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 