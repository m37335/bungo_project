#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫API実用クライアント
仕様書 bungo_update_spec_draft01.md S2章 青空文庫パイプラインに基づく実装

使用API: aozorahack.org の無料API
"""

import requests
import re
import time
import os
import csv
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin, quote
import json
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AozoraAPIClient:
    """青空文庫API実用クライアント"""
    
    def __init__(self, cache_dir: str = "aozora_cache"):
        self.api_base = "https://pubserver1.herokuapp.com/api/v0.1"
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BungoMapSystem/1.0 (Educational Research)'
        })
        
        # キャッシュディレクトリ作成
        os.makedirs(cache_dir, exist_ok=True)
        
    def search_books(self, author: str = "", title: str = "") -> List[Dict]:
        """作品検索"""
        try:
            url = f"{self.api_base}/books"
            params = {}
            if author:
                params['author'] = author
            if title:
                params['title'] = title
                
            self.logger.info(f"青空文庫API検索: {params}")
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                books = data.get('books', [])
                self.logger.info(f"検索結果: {len(books)}件")
                return books
            else:
                self.logger.warning(f"API検索失敗: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"検索エラー: {e}")
            return []
    
    def get_book_text(self, book_id: str) -> Optional[str]:
        """テキスト取得"""
        try:
            url = f"{self.api_base}/books/{book_id}.txt"
            self.logger.info(f"テキスト取得: {book_id}")
            
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                # 文字エンコーディング検出
                text = response.content.decode('utf-8', errors='ignore')
                self.logger.info(f"テキスト取得成功: {len(text)}文字")
                return text
            else:
                self.logger.warning(f"テキスト取得失敗: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"テキスト取得エラー: {e}")
            return None
    
    def cache_text(self, book_id: str, text: str) -> str:
        """テキストキャッシュ保存"""
        cache_file = Path(self.cache_dir) / f"{book_id}.txt"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(text)
            self.logger.info(f"キャッシュ保存: {cache_file}")
            return str(cache_file)
        except Exception as e:
            self.logger.error(f"キャッシュ保存エラー: {e}")
            return ""
    
    def load_cached_text(self, book_id: str) -> Optional[str]:
        """キャッシュからテキスト読み込み"""
        cache_file = Path(self.cache_dir) / f"{book_id}.txt"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                self.logger.info(f"キャッシュ読み込み: {cache_file}")
                return text
            except Exception as e:
                self.logger.error(f"キャッシュ読み込みエラー: {e}")
        return None
    
    def fetch_work_with_cache(self, author_name: str, work_title: str) -> Optional[Dict]:
        """キャッシュ機能付き作品取得"""
        # 検索
        books = self.search_books(author=author_name, title=work_title)
        if not books:
            self.logger.warning(f"作品が見つかりません: {author_name} - {work_title}")
            return None
        
        # 最適な候補を選択
        best_match = None
        for book in books:
            if author_name in book.get('author', '') and work_title in book.get('title', ''):
                best_match = book
                break
        
        if not best_match:
            best_match = books[0]  # 最初の候補を使用
        
        book_id = best_match['book_id']
        
        # キャッシュ確認
        text = self.load_cached_text(book_id)
        if text:
            best_match['text'] = text
            best_match['cache_hit'] = True
            return best_match
        
        # APIからテキスト取得
        text = self.get_book_text(book_id)
        if text:
            self.cache_text(book_id, text)
            best_match['text'] = text
            best_match['cache_hit'] = False
            time.sleep(1)  # API負荷軽減
            return best_match
        
        return None

def test_aozora_api():
    """青空文庫API動作テスト"""
    print("🧪 青空文庫API動作テスト開始")
    
    client = AozoraAPIClient()
    
    # テストケース1: 夏目漱石 作品検索
    print("\n📚 テスト1: 夏目漱石 作品検索")
    books = client.search_books(author="夏目漱石")
    print(f"検索結果: {len(books)}件")
    if books:
        for i, book in enumerate(books[:5]):  # 最初の5件表示
            print(f"  {i+1}. {book.get('title', '不明')} (ID: {book.get('book_id', '不明')})")
    
    # テストケース2: 坊っちゃん テキスト取得
    print("\n📖 テスト2: 坊っちゃん テキスト取得")
    work = client.fetch_work_with_cache("夏目漱石", "坊っちゃん")
    if work:
        text = work.get('text', '')
        print(f"取得成功: {work.get('title')} ({len(text)}文字)")
        print(f"キャッシュ: {'ヒット' if work.get('cache_hit') else 'ミス'}")
        print(f"テキスト冒頭: {text[:100]}...")
    else:
        print("取得失敗")
    
    print("\n✅ 青空文庫APIテスト完了")

if __name__ == "__main__":
    test_aozora_api() 