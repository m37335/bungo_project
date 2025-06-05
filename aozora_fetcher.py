#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫テキスト取得API
仕様書 bungo_update_spec_draft01.md S2章 青空文庫パイプラインに基づく実装
"""

import requests
import re
import time
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin, quote
import json
from bs4 import BeautifulSoup
import zipfile
import io
import os

class AozoraFetcher:
    """青空文庫テキスト取得クライアント"""
    
    def __init__(self, cache_dir: str = "aozora_cache"):
        self.base_url = "https://www.aozora.gr.jp"
        self.api_url = "https://pubserver1.herokuapp.com/api/v0.1/books"
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BungoMapSystem/1.0 (Educational Research Purpose)'
        })
        
        # キャッシュディレクトリ作成
        os.makedirs(cache_dir, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
    
    def search_author_works(self, author_name: str) -> List[Dict]:
        """
        作者名で作品検索
        
        Args:
            author_name: 作者名
            
        Returns:
            作品リスト（タイトル、ID、URL等）
        """
        self.logger.info(f"🔍 青空文庫検索: {author_name}")
        
        try:
            # 青空文庫API検索
            params = {'author': author_name}
            response = self.session.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            books = response.json()
            
            if not books:
                self.logger.warning(f"❌ 検索結果なし: {author_name}")
                return []
            
            works = []
            for book in books[:10]:  # 最大10作品
                work_info = {
                    'book_id': book.get('book_id'),
                    'title': book.get('title'),
                    'author': book.get('authors', [{}])[0].get('last_name', '') + book.get('authors', [{}])[0].get('first_name', ''),
                    'text_url': book.get('text_url'),
                    'html_url': book.get('html_url'),
                    'card_url': book.get('card_url'),
                    'release_date': book.get('release_date'),
                    'input_encoding': book.get('input_encoding', 'Shift_JIS')
                }
                works.append(work_info)
            
            self.logger.info(f"✅ 検索完了: {author_name} - {len(works)}作品発見")
            return works
            
        except requests.RequestException as e:
            self.logger.error(f"❌ API検索エラー {author_name}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ 検索処理エラー {author_name}: {e}")
            return []
    
    def get_text_content(self, work_info: Dict) -> Optional[str]:
        """
        作品の本文テキスト取得
        
        Args:
            work_info: search_author_works()の結果の1つ
            
        Returns:
            本文テキスト（青空文庫記法除去済み）
        """
        book_id = work_info.get('book_id')
        title = work_info.get('title')
        text_url = work_info.get('text_url')
        
        if not text_url:
            self.logger.warning(f"❌ テキストURL未取得: {title}")
            return None
        
        self.logger.info(f"📥 テキスト取得開始: {title}")
        
        # キャッシュファイル確認
        cache_file = os.path.join(self.cache_dir, f"{book_id}_{title}.txt")
        if os.path.exists(cache_file):
            self.logger.info(f"📁 キャッシュから読み込み: {title}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        try:
            # テキストファイル取得
            response = self.session.get(text_url, timeout=30)
            response.raise_for_status()
            
            # エンコーディング検出・変換
            encoding = work_info.get('input_encoding', 'shift_jis')
            try:
                text_content = response.content.decode(encoding)
            except UnicodeDecodeError:
                # フォールバック
                text_content = response.content.decode('shift_jis', errors='ignore')
            
            # 青空文庫記法除去
            cleaned_text = self._clean_aozora_text(text_content)
            
            # キャッシュ保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            self.logger.info(f"✅ テキスト取得完了: {title} ({len(cleaned_text)}文字)")
            return cleaned_text
            
        except requests.RequestException as e:
            self.logger.error(f"❌ テキスト取得エラー {title}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ テキスト処理エラー {title}: {e}")
            return None
    
    def _clean_aozora_text(self, raw_text: str) -> str:
        """
        青空文庫記法除去
        
        Args:
            raw_text: 生テキスト
            
        Returns:
            記法除去済みテキスト
        """
        # 基本的な青空文庫記法を除去
        patterns = [
            r'-------------------------------------------------------.*?-------------------------------------------------------',  # ヘッダー・フッター
            r'底本：.*?\n',  # 底本情報
            r'入力：.*?\n',  # 入力者情報
            r'校正：.*?\n',  # 校正者情報
            r'※.*?\n',      # 注釈行
            r'［＃.*?］',   # 記法タグ
            r'｜',          # ルビ開始記号
            r'《.*?》',     # ルビ
            r'〔.*?〕',     # 編者注
        ]
        
        cleaned = raw_text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
        
        # 余分な空白・改行整理
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        cleaned = re.sub(r'　+', '　', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def get_multiple_works_text(self, author_name: str, max_works: int = 5) -> List[Dict]:
        """
        指定作者の複数作品テキスト一括取得
        
        Args:
            author_name: 作者名
            max_works: 最大取得作品数
            
        Returns:
            作品テキストリスト
        """
        self.logger.info(f"📚 複数作品取得開始: {author_name} (最大{max_works}作品)")
        
        # 作品検索
        works = self.search_author_works(author_name)
        if not works:
            return []
        
        results = []
        for i, work in enumerate(works[:max_works]):
            self.logger.info(f"📖 取得中 {i+1}/{min(len(works), max_works)}: {work['title']}")
            
            text_content = self.get_text_content(work)
            if text_content:
                results.append({
                    'author': author_name,
                    'title': work['title'],
                    'book_id': work['book_id'],
                    'text_content': text_content,
                    'char_count': len(text_content),
                    'aozora_url': work.get('card_url', ''),
                    'release_date': work.get('release_date')
                })
            
            # レート制限（礼儀）
            time.sleep(1)
        
        self.logger.info(f"✅ 複数作品取得完了: {author_name} - {len(results)}作品")
        return results
    
    def get_author_profile(self, author_name: str) -> Optional[Dict]:
        """
        作者プロフィール情報取得
        
        Args:
            author_name: 作者名
            
        Returns:
            作者情報（生年月日等）
        """
        try:
            # 青空文庫の作者検索
            search_url = f"{self.base_url}/index_pages/person_search.html"
            
            # 簡易実装（実際はより複雑な検索が必要）
            return {
                'name': author_name,
                'birth_year': None,
                'death_year': None,
                'profile_url': f"{self.base_url}/index_pages/person_search.html"
            }
            
        except Exception as e:
            self.logger.error(f"❌ プロフィール取得エラー {author_name}: {e}")
            return None

def test_aozora_fetcher():
    """青空文庫取得テスト"""
    print("🧪 青空文庫取得テスト開始")
    
    fetcher = AozoraFetcher()
    
    # 夏目漱石作品検索
    print("\n1. 作品検索テスト")
    works = fetcher.search_author_works("夏目漱石")
    print(f"検索結果: {len(works)}作品")
    for work in works[:3]:
        print(f"  - {work['title']} (ID: {work['book_id']})")
    
    # テキスト取得テスト
    if works:
        print("\n2. テキスト取得テスト")
        first_work = works[0]
        text = fetcher.get_text_content(first_work)
        if text:
            print(f"テキスト取得成功: {first_work['title']}")
            print(f"文字数: {len(text)}")
            print(f"冒頭: {text[:200]}...")
        else:
            print("テキスト取得失敗")
    
    # 複数作品取得テスト
    print("\n3. 複数作品取得テスト")
    results = fetcher.get_multiple_works_text("夏目漱石", max_works=2)
    print(f"取得完了: {len(results)}作品")
    for result in results:
        print(f"  - {result['title']}: {result['char_count']}文字")
    
    print("✅ テスト完了")

if __name__ == "__main__":
    test_aozora_fetcher() 