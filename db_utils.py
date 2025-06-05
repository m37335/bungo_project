#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースユーティリティ（SQLite & Google Sheets統一インターフェース）
仕様書 bungo_update_spec_draft01.md 5章モジュール構成に基づく実装
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple
import logging

# Google Sheets連携（オプション）
try:
    import gspread
    from google.auth import default
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

class BungoDatabase:
    """文豪データベース統一インターフェース"""
    
    def __init__(self, db_type: str = "sqlite", db_path: str = "bungo.db"):
        """
        Args:
            db_type: "sqlite" or "sheets"
            db_path: SQLiteファイルパスまたはSpreadsheetID
        """
        self.db_type = db_type
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        if db_type == "sqlite":
            self._init_sqlite()
        elif db_type == "sheets":
            self._init_sheets()
        else:
            raise ValueError(f"未対応のDB種別: {db_type}")
    
    def _init_sqlite(self):
        """SQLite初期化"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # スキーマ作成
        schema_file = "db_schema.sql"
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = f.read()
                self.conn.executescript(schema)
                self.conn.commit()
                self.logger.info(f"✅ SQLiteスキーマ初期化完了: {self.db_path}")
    
    def _init_sheets(self):
        """Google Sheets初期化"""
        if not GSPREAD_AVAILABLE:
            raise ImportError("Google Sheetsを使用するにはgspreadをインストールしてください")
        
        # 認証とスプレッドシート接続
        self.gc = gspread.service_account()
        self.spreadsheet = self.gc.open_by_key(self.db_path)
        self.logger.info(f"✅ Google Sheets接続完了: {self.db_path}")
    
    def insert_author(self, name: str, wikipedia_url: str = None, 
                     birth_year: int = None, death_year: int = None) -> int:
        """作者挿入"""
        if self.db_type == "sqlite":
            cursor = self.conn.execute(
                """INSERT OR IGNORE INTO authors (name, wikipedia_url, birth_year, death_year) 
                   VALUES (?, ?, ?, ?)""",
                (name, wikipedia_url, birth_year, death_year)
            )
            self.conn.commit()
            return cursor.lastrowid or self._get_author_id(name)
        
        elif self.db_type == "sheets":
            # Sheetsの場合は authors シートに追加
            try:
                authors_sheet = self.spreadsheet.worksheet("authors")
            except:
                authors_sheet = self.spreadsheet.add_worksheet("authors", rows=1000, cols=10)
                authors_sheet.update("A1:G1", [["author_id", "name", "wikipedia_url", "birth_year", "death_year", "created_at", "updated_at"]])
            
            # 既存チェック
            existing_authors = authors_sheet.get_all_records()
            for i, author in enumerate(existing_authors):
                if author['name'] == name:
                    return author['author_id']
            
            # 新規追加
            author_id = len(existing_authors) + 1
            authors_sheet.append_row([
                author_id, name, wikipedia_url or "", birth_year or "", 
                death_year or "", datetime.now().isoformat(), datetime.now().isoformat()
            ])
            return author_id
    
    def _get_author_id(self, name: str) -> Optional[int]:
        """作者ID取得"""
        if self.db_type == "sqlite":
            cursor = self.conn.execute("SELECT author_id FROM authors WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def insert_work(self, author_id: int, title: str, wikipedia_url: str = None,
                   aozora_url: str = None, publication_year: int = None, genre: str = None) -> int:
        """作品挿入"""
        if self.db_type == "sqlite":
            cursor = self.conn.execute(
                """INSERT OR IGNORE INTO works (author_id, title, wikipedia_url, aozora_url, publication_year, genre)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (author_id, title, wikipedia_url, aozora_url, publication_year, genre)
            )
            self.conn.commit()
            return cursor.lastrowid or self._get_work_id(author_id, title)
        
        elif self.db_type == "sheets":
            try:
                works_sheet = self.spreadsheet.worksheet("works")
            except:
                works_sheet = self.spreadsheet.add_worksheet("works", rows=1000, cols=15)
                works_sheet.update("A1:I1", [["work_id", "author_id", "title", "wikipedia_url", "aozora_url", "publication_year", "genre", "created_at", "updated_at"]])
            
            # 既存チェック
            existing_works = works_sheet.get_all_records()
            for work in existing_works:
                if work['author_id'] == author_id and work['title'] == title:
                    return work['work_id']
            
            # 新規追加
            work_id = len(existing_works) + 1
            works_sheet.append_row([
                work_id, author_id, title, wikipedia_url or "", aozora_url or "",
                publication_year or "", genre or "", datetime.now().isoformat(), datetime.now().isoformat()
            ])
            return work_id
    
    def _get_work_id(self, author_id: int, title: str) -> Optional[int]:
        """作品ID取得"""
        if self.db_type == "sqlite":
            cursor = self.conn.execute("SELECT work_id FROM works WHERE author_id = ? AND title = ?", (author_id, title))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def upsert_place(self, work_id: int, place_name: str, latitude: float = None, longitude: float = None,
                    address: str = None, before_text: str = None, sentence: str = None, after_text: str = None,
                    extraction_method: str = "llm", confidence: float = 0.8, maps_url: str = None) -> int:
        """地名挿入・更新"""
        if self.db_type == "sqlite":
            # 既存チェック
            cursor = self.conn.execute("SELECT place_id FROM places WHERE work_id = ? AND place_name = ?", (work_id, place_name))
            existing = cursor.fetchone()
            
            if existing:
                # 更新
                self.conn.execute(
                    """UPDATE places SET latitude = ?, longitude = ?, address = ?, before_text = ?, 
                       sentence = ?, after_text = ?, extraction_method = ?, confidence = ?, 
                       maps_url = ?, geocoded = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE place_id = ?""",
                    (latitude, longitude, address, before_text, sentence, after_text, 
                     extraction_method, confidence, maps_url, latitude is not None, existing[0])
                )
                self.conn.commit()
                return existing[0]
            else:
                # 新規挿入
                cursor = self.conn.execute(
                    """INSERT INTO places (work_id, place_name, latitude, longitude, address, before_text,
                       sentence, after_text, extraction_method, confidence, maps_url, geocoded)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (work_id, place_name, latitude, longitude, address, before_text, sentence, after_text,
                     extraction_method, confidence, maps_url, latitude is not None)
                )
                self.conn.commit()
                return cursor.lastrowid
    
    def search_authors(self, query: str) -> List[Dict]:
        """作者検索"""
        if self.db_type == "sqlite":
            cursor = self.conn.execute(
                "SELECT * FROM authors WHERE name LIKE ? ORDER BY name",
                (f"%{query}%",)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def search_works(self, query: str) -> List[Dict]:
        """作品検索"""
        if self.db_type == "sqlite":
            cursor = self.conn.execute(
                """SELECT w.*, a.name as author_name FROM works w 
                   JOIN authors a ON w.author_id = a.author_id
                   WHERE w.title LIKE ? ORDER BY a.name, w.title""",
                (f"%{query}%",)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def search_places(self, query: str) -> List[Dict]:
        """地名検索"""
        if self.db_type == "sqlite":
            cursor = self.conn.execute(
                """SELECT * FROM bungo_integrated WHERE place_name LIKE ? ORDER BY author_name, work_title""",
                (f"%{query}%",)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_places(self) -> pd.DataFrame:
        """全地名データをDataFrameで取得"""
        if self.db_type == "sqlite":
            return pd.read_sql_query("SELECT * FROM bungo_integrated", self.conn)
    
    def export_to_csv(self, filename: str = "bungo_database_export.csv"):
        """CSV出力"""
        df = self.get_all_places()
        df.to_csv(filename, index=False, encoding='utf-8')
        self.logger.info(f"✅ CSV出力完了: {filename} ({len(df)}件)")
        return filename
    
    def get_stats(self) -> Dict:
        """統計情報取得"""
        if self.db_type == "sqlite":
            stats = {}
            stats['authors_count'] = self.conn.execute("SELECT COUNT(*) FROM authors").fetchone()[0]
            stats['works_count'] = self.conn.execute("SELECT COUNT(*) FROM works").fetchone()[0]
            stats['places_count'] = self.conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
            stats['geocoded_count'] = self.conn.execute("SELECT COUNT(*) FROM places WHERE geocoded = 1").fetchone()[0]
            stats['geocoded_rate'] = (stats['geocoded_count'] / stats['places_count'] * 100) if stats['places_count'] > 0 else 0
            return stats
    
    def close(self):
        """接続クローズ"""
        if self.db_type == "sqlite" and hasattr(self, 'conn'):
            self.conn.close()
            self.logger.info("✅ SQLite接続クローズ")

# 使用例・テスト用関数
def test_database():
    """データベース動作テスト"""
    print("🧪 データベーステスト開始")
    
    # SQLite版テスト
    db = BungoDatabase("sqlite", "test_bungo.db")
    
    # 作者追加
    author_id = db.insert_author("夏目漱石", "https://ja.wikipedia.org/wiki/夏目漱石", 1867, 1916)
    print(f"作者ID: {author_id}")
    
    # 作品追加
    work_id = db.insert_work(author_id, "坊っちゃん", genre="小説")
    print(f"作品ID: {work_id}")
    
    # 地名追加
    place_id = db.upsert_place(work_id, "松山市", 33.84, 132.77, "愛媛県松山市", 
                              sentence="四国は松山の中学校に数学の教師として赴任することになった。")
    print(f"地名ID: {place_id}")
    
    # 検索テスト
    authors = db.search_authors("夏目")
    print(f"作者検索結果: {len(authors)}件")
    
    places = db.search_places("松山")
    print(f"地名検索結果: {len(places)}件")
    
    # 統計
    stats = db.get_stats()
    print(f"統計: {stats}")
    
    db.close()
    print("✅ テスト完了")

if __name__ == "__main__":
    test_database() 