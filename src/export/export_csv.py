#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV エクスポート機能
データベース内容をCSVファイルに出力
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from db_utils import BungoDatabase

class CSVExporter:
    """CSV エクスポートクラス"""
    
    def __init__(self, db_path: str = "test_ginza.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def export_authors(self, filename: Optional[str] = None) -> str:
        """作者データをCSVエクスポート"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"authors_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        db = BungoDatabase("sqlite", self.db_path)
        authors = db.search_authors("")  # 全作者取得
        db.close()
        
        # CSVヘッダー
        fieldnames = ['author_id', 'name', 'birth_year', 'death_year', 'wikipedia_url']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for author in authors:
                writer.writerow({
                    'author_id': author.get('author_id', ''),
                    'name': author.get('name', ''),
                    'birth_year': author.get('birth_year', ''),
                    'death_year': author.get('death_year', ''),
                    'wikipedia_url': author.get('wikipedia_url', '')
                })
        
        print(f"✅ 作者データCSVエクスポート完了: {filepath}")
        print(f"   件数: {len(authors)}件")
        return str(filepath)
    
    def export_works(self, filename: Optional[str] = None) -> str:
        """作品データをCSVエクスポート"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"works_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        db = BungoDatabase("sqlite", self.db_path)
        works = db.search_works("")  # 全作品取得
        db.close()
        
        # CSVヘッダー
        fieldnames = ['work_id', 'author_id', 'author_name', 'title', 'publication_year', 'genre', 'aozora_url']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for work in works:
                writer.writerow({
                    'work_id': work.get('work_id', ''),
                    'author_id': work.get('author_id', ''),
                    'author_name': work.get('author_name', ''),
                    'title': work.get('title', ''),
                    'publication_year': work.get('publication_year', ''),
                    'genre': work.get('genre', ''),
                    'aozora_url': work.get('aozora_url', '')
                })
        
        print(f"✅ 作品データCSVエクスポート完了: {filepath}")
        print(f"   件数: {len(works)}件")
        return str(filepath)
    
    def export_places(self, filename: Optional[str] = None, geocoded_only: bool = False) -> str:
        """地名データをCSVエクスポート"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_geocoded" if geocoded_only else ""
            filename = f"places{suffix}_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        db = BungoDatabase("sqlite", self.db_path)
        places = db.search_places("")  # 全地名取得
        db.close()
        
        # フィルタリング
        if geocoded_only:
            places = [p for p in places if p.get('latitude') and p.get('longitude')]
        
        # CSVヘッダー
        fieldnames = [
            'place_id', 'work_id', 'author_name', 'work_title', 'place_name',
            'latitude', 'longitude', 'address', 'sentence', 'before_text', 'after_text',
            'relevance_score', 'maps_url'
        ]
        
        with open(filepath, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for place in places:
                writer.writerow({
                    'place_id': place.get('place_id', ''),
                    'work_id': place.get('work_id', ''),
                    'author_name': place.get('author_name', ''),
                    'work_title': place.get('work_title', ''),
                    'place_name': place.get('place_name', ''),
                    'latitude': place.get('latitude', ''),
                    'longitude': place.get('longitude', ''),
                    'address': place.get('address', ''),
                    'sentence': place.get('sentence', ''),
                    'before_text': place.get('before_text', ''),
                    'after_text': place.get('after_text', ''),
                    'relevance_score': place.get('relevance_score', ''),
                    'maps_url': place.get('maps_url', '')
                })
        
        print(f"✅ 地名データCSVエクスポート完了: {filepath}")
        print(f"   件数: {len(places)}件")
        if geocoded_only:
            print(f"   （ジオコーディング済みのみ）")
        return str(filepath)
    
    def export_combined_data(self, filename: Optional[str] = None, author_filter: Optional[str] = None, 
                           work_filter: Optional[str] = None) -> str:
        """結合データをCSVエクスポート（作者-作品-地名の関連データ）"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bungo_combined_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        db = BungoDatabase("sqlite", self.db_path)
        
        # 結合クエリで全データ取得
        query = """
        SELECT 
            a.name as author_name,
            a.birth_year,
            a.death_year,
            w.title as work_title,
            w.publication_year,
            w.genre,
            w.aozora_url,
            p.place_name,
            p.latitude,
            p.longitude,
            p.address,
            p.sentence,
            p.before_text,
            p.after_text
        FROM places p
        LEFT JOIN works w ON p.work_id = w.work_id
        LEFT JOIN authors a ON w.author_id = a.author_id
        """
        
        # フィルタ条件追加
        conditions = []
        if author_filter:
            conditions.append(f"a.name LIKE '%{author_filter}%'")
        if work_filter:
            conditions.append(f"w.title LIKE '%{work_filter}%'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY a.name, w.title, p.place_name"
        
        # データ取得
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        conn.close()
        db.close()
        
        # CSVヘッダー
        fieldnames = [
            'author_name', 'birth_year', 'death_year',
            'work_title', 'publication_year', 'genre', 'aozora_url',
            'place_name', 'latitude', 'longitude', 'address',
            'sentence', 'before_text', 'after_text'
        ]
        
        with open(filepath, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in rows:
                writer.writerow(dict(row))
        
        print(f"✅ 結合データCSVエクスポート完了: {filepath}")
        print(f"   件数: {len(rows)}件")
        if author_filter:
            print(f"   作者フィルタ: {author_filter}")
        if work_filter:
            print(f"   作品フィルタ: {work_filter}")
        return str(filepath)
    
    def export_all(self, prefix: Optional[str] = None) -> Dict[str, str]:
        """全データを一括エクスポート"""
        if not prefix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"bungo_export_{timestamp}"
        
        print(f"🚀 文豪ゆかり地図システム - 全データCSVエクスポート開始")
        print(f"出力ディレクトリ: {self.output_dir}")
        print("=" * 50)
        
        results = {}
        
        # 各テーブルをエクスポート
        results['authors'] = self.export_authors(f"{prefix}_authors.csv")
        results['works'] = self.export_works(f"{prefix}_works.csv")
        results['places'] = self.export_places(f"{prefix}_places.csv")
        results['places_geocoded'] = self.export_places(f"{prefix}_places_geocoded.csv", geocoded_only=True)
        results['combined'] = self.export_combined_data(f"{prefix}_combined.csv")
        
        print("=" * 50)
        print(f"🎉 全データCSVエクスポート完了！")
        print(f"出力ファイル数: {len(results)}件")
        
        return results
    
    def get_export_stats(self) -> Dict[str, int]:
        """エクスポート統計情報取得"""
        db = BungoDatabase("sqlite", self.db_path)
        
        authors = db.search_authors("")
        works = db.search_works("")
        places = db.search_places("")
        geocoded_places = [p for p in places if p.get('latitude') and p.get('longitude')]
        
        db.close()
        
        return {
            'authors_count': len(authors),
            'works_count': len(works),
            'places_count': len(places),
            'geocoded_places_count': len(geocoded_places),
            'geocoding_rate': (len(geocoded_places) / len(places) * 100) if places else 0
        }


def export_db_to_csv(db_path: str = "test_ginza.db", output_dir: str = "output", 
                     export_type: str = "all", **kwargs) -> Dict[str, str]:
    """
    データベースをCSVにエクスポートする便利関数
    
    Args:
        db_path: データベースパス
        output_dir: 出力ディレクトリ
        export_type: エクスポート種別 ("all", "authors", "works", "places", "combined")
        **kwargs: 追加オプション
    
    Returns:
        エクスポートされたファイルパスの辞書
    """
    exporter = CSVExporter(db_path, output_dir)
    
    if export_type == "all":
        return exporter.export_all(kwargs.get('prefix'))
    elif export_type == "authors":
        return {'authors': exporter.export_authors(kwargs.get('filename'))}
    elif export_type == "works":
        return {'works': exporter.export_works(kwargs.get('filename'))}
    elif export_type == "places":
        return {'places': exporter.export_places(kwargs.get('filename'), kwargs.get('geocoded_only', False))}
    elif export_type == "combined":
        return {'combined': exporter.export_combined_data(
            kwargs.get('filename'), 
            kwargs.get('author_filter'), 
            kwargs.get('work_filter')
        )}
    else:
        raise ValueError(f"未対応のエクスポート種別: {export_type}")


def main():
    """メイン実行（CLIテスト用）"""
    import argparse
    
    parser = argparse.ArgumentParser(description="文豪ゆかり地図システム CSV エクスポート")
    parser.add_argument("--db", default="test_ginza.db", help="データベースパス")
    parser.add_argument("--output", default="output", help="出力ディレクトリ")
    parser.add_argument("--type", choices=["all", "authors", "works", "places", "combined"], 
                       default="all", help="エクスポート種別")
    parser.add_argument("--author", help="作者フィルタ（combined時のみ）")
    parser.add_argument("--work", help="作品フィルタ（combined時のみ）")
    parser.add_argument("--geocoded-only", action="store_true", help="ジオコーディング済みのみ（places時のみ）")
    
    args = parser.parse_args()
    
    # エクスポート実行
    exporter = CSVExporter(args.db, args.output)
    
    # 統計表示
    stats = exporter.get_export_stats()
    print(f"📊 データベース統計:")
    print(f"   作者: {stats['authors_count']}名")
    print(f"   作品: {stats['works_count']}件")
    print(f"   地名: {stats['places_count']}箇所")
    print(f"   ジオコーディング済み: {stats['geocoded_places_count']}箇所 ({stats['geocoding_rate']:.1f}%)")
    print()
    
    # エクスポート実行
    results = export_db_to_csv(
        db_path=args.db,
        output_dir=args.output,
        export_type=args.type,
        author_filter=args.author,
        work_filter=args.work,
        geocoded_only=args.geocoded_only
    )
    
    print(f"\n📁 エクスポート結果:")
    for export_type, filepath in results.items():
        print(f"   {export_type}: {filepath}")


if __name__ == "__main__":
    main() 