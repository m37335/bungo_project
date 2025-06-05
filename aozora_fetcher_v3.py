#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫テキスト取得システム（GitHubミラー版）
仕様書 bungo_update_spec_draft01.md S2章 青空文庫パイプラインに基づく実装

参考：
- GitHub aozorahack/aozorabunko_text (テキストのみ版)
- aozorahack.org (個別アクセス可能)
"""

import requests
import re
import time
import os
import csv
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin, quote, unquote
import json
from pathlib import Path
import chardet

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AozoraFetcherV3:
    """青空文庫テキスト取得クライアント（GitHubミラー版）"""
    
    def __init__(self, cache_dir: str = "aozora_cache"):
        # GitHub aozorahack/aozorabunko_text のRAWファイルアクセス
        self.github_base = "https://raw.githubusercontent.com/aozorahack/aozorabunko_text/master/cards"
        
        # aozorahack.org の直接アクセス
        self.aozorahack_base = "https://aozorahack.org/aozorabunko_text/cards"
        
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BungoMapSystem/1.0 (Educational Research Purpose)'
        })
        
        # キャッシュディレクトリ作成
        os.makedirs(cache_dir, exist_ok=True)
        
    def detect_encoding(self, content: bytes) -> str:
        """文字エンコーディングを検出"""
        detected = chardet.detect(content)
        confidence = detected.get('confidence', 0)
        encoding = detected.get('encoding', 'shift_jis')
        
        # 青空文庫は通常Shift_JISなので、自信がない場合はShift_JISを使用
        if confidence < 0.7:
            encoding = 'shift_jis'
            
        self.logger.debug(f"エンコーディング検出: {encoding} (信頼度: {confidence})")
        return encoding
    
    def search_author_works(self, author_name: str) -> List[Dict[str, str]]:
        """
        作者名から作品情報を検索
        Note: 実際の実装では、青空文庫のCSVデータから検索するか、
        既存のDBから検索する方が効率的
        """
        self.logger.info(f"作者検索: {author_name}")
        
        # 既存データベースから検索する（実際のデータを使用）
        try:
            from db_utils import BungoDatabase
            db = BungoDatabase(db_type="sqlite", db_path="bungo_production.db")
            results = db.search_authors(author_name)
            
            works = []
            for author in results:
                author_works = db.search_works("")  # 全作品を取得してフィルタ
                for work in author_works:
                    if work['author_name'] == author['name']:
                        works.append({
                            'author_id': str(author['author_id']).zfill(6),
                            'work_id': str(work['work_id']),
                            'author_name': work['author_name'],
                            'title': work['title'],
                            'estimated_file_path': self._estimate_file_path(author['author_id'], work['work_id'])
                        })
            
            db.close()
            return works
            
        except Exception as e:
            self.logger.warning(f"DB検索失敗: {e}, デモデータを返します")
            # デモデータ（夏目漱石の例）
            if "夏目" in author_name or "漱石" in author_name:
                return [{
                    'author_id': '000148',
                    'work_id': '789',
                    'author_name': '夏目漱石',
                    'title': '吾輩は猫である',
                    'estimated_file_path': '000148/files/789_ruby_5639'
                }]
            return []
    
    def _estimate_file_path(self, author_id: int, work_id: int) -> str:
        """作品IDからファイルパスを推定"""
        author_id_str = str(author_id).zfill(6)
        work_id_str = str(work_id)
        
        # 青空文庫の一般的なパターン：000148/files/789_ruby_5639 など
        return f"{author_id_str}/files/{work_id_str}_ruby_*"
    
    def fetch_text_content(self, author_id: str, work_id: str, title: str = "") -> Optional[str]:
        """
        指定された作品のテキストを取得
        """
        self.logger.info(f"テキスト取得開始: 作者ID={author_id}, 作品ID={work_id}, タイトル={title}")
        
        # キャッシュチェック
        cache_file = os.path.join(self.cache_dir, f"{author_id}_{work_id}.txt")
        if os.path.exists(cache_file):
            self.logger.info(f"キャッシュから読み込み: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # 複数のファイル名パターンを試行
        file_patterns = [
            f"{work_id}_ruby_*.txt",  # ルビ版
            f"{work_id}_txt_*.txt",   # テキスト版
            f"{work_id}.txt"          # シンプル版
        ]
        
        for pattern in file_patterns:
            content = self._try_fetch_pattern(author_id, work_id, pattern)
            if content:
                # キャッシュに保存
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.info(f"テキスト取得成功: {len(content)}文字")
                return content
        
        self.logger.warning(f"テキスト取得失敗: 作者ID={author_id}, 作品ID={work_id}")
        return None
    
    def _try_fetch_pattern(self, author_id: str, work_id: str, filename_pattern: str) -> Optional[str]:
        """特定のファイル名パターンでテキスト取得を試行"""
        
        # いくつかの一般的なパターンを試行
        common_suffixes = ["ruby_5639", "txt_23610", "ruby_44732", "txt_15567"]
        
        for suffix in common_suffixes:
            if "*" in filename_pattern:
                filename = filename_pattern.replace("*", suffix)
            else:
                filename = filename_pattern
            
            # GitHubミラーから試行
            github_url = f"{self.github_base}/{author_id}/files/{work_id}_{suffix}/{filename}"
            content = self._fetch_from_url(github_url)
            if content:
                return content
            
            # aozorahack.orgから試行
            aozorahack_url = f"{self.aozorahack_base}/{author_id}/files/{work_id}_{suffix}/{filename}"
            content = self._fetch_from_url(aozorahack_url)
            if content:
                return content
        
        return None
    
    def _fetch_from_url(self, url: str) -> Optional[str]:
        """指定URLからテキストを取得"""
        try:
            self.logger.debug(f"URL取得試行: {url}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # エンコーディング検出・変換
                encoding = self.detect_encoding(response.content)
                content = response.content.decode(encoding, errors='ignore')
                
                # 青空文庫の基本的な妥当性チェック
                if self._is_valid_aozora_text(content):
                    self.logger.debug(f"URL取得成功: {url}")
                    return content
                else:
                    self.logger.debug(f"無効なテキスト形式: {url}")
            else:
                self.logger.debug(f"URL取得失敗 ({response.status_code}): {url}")
                
        except Exception as e:
            self.logger.debug(f"URL取得エラー: {url} - {e}")
        
        return None
    
    def _is_valid_aozora_text(self, content: str) -> bool:
        """青空文庫テキストの妥当性をチェック"""
        if not content or len(content) < 100:
            return False
        
        # 青空文庫特有の記法があるかチェック
        aozora_markers = [
            "-------------------------------------------------------",
            "青空文庫",
            "※［＃",
            "《",
            "》"
        ]
        
        # いずれかのマーカーが含まれていれば青空文庫テキストと判定
        for marker in aozora_markers:
            if marker in content:
                return True
        
        # 日本語テキストかどうかの基本チェック
        japanese_chars = sum(1 for c in content[:1000] if '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF')
        return japanese_chars > 50
    
    def extract_title_and_author(self, content: str) -> Dict[str, str]:
        """テキストからタイトルと作者を抽出"""
        info = {'title': '', 'author': ''}
        
        lines = content.split('\n')
        for i, line in enumerate(lines[:20]):  # 最初の20行をチェック
            line = line.strip()
            
            # タイトル抽出（通常は最初の空でない行）
            if not info['title'] and line and not line.startswith('-') and not line.startswith('※'):
                info['title'] = line
            
            # 作者抽出（「著者」「作者」などのキーワードを探す）
            if '著者' in line or '作者' in line:
                author_match = re.search(r'(?:著者|作者)[:：]?\s*(.+)', line)
                if author_match:
                    info['author'] = author_match.group(1).strip()
        
        return info

# テスト実行部分
def test_aozora_fetcher():
    """青空文庫取得のテスト"""
    print("🚀 青空文庫テキスト取得テスト開始")
    
    fetcher = AozoraFetcherV3()
    
    # 1. 作者検索テスト
    print("\n📚 作者検索テスト:")
    works = fetcher.search_author_works("夏目漱石")
    for work in works:
        print(f"  - {work['title']} ({work['author_name']})")
        print(f"    作者ID: {work['author_id']}, 作品ID: {work['work_id']}")
    
    # 2. テキスト取得テスト
    if works:
        print(f"\n📖 テキスト取得テスト: {works[0]['title']}")
        work = works[0]
        content = fetcher.fetch_text_content(
            work['author_id'], 
            work['work_id'], 
            work['title']
        )
        
        if content:
            print(f"✅ テキスト取得成功: {len(content)}文字")
            
            # テキスト解析
            info = fetcher.extract_title_and_author(content)
            print(f"  抽出タイトル: {info['title']}")
            print(f"  抽出作者: {info['author']}")
            
            # 冒頭表示
            preview = content[:200].replace('\n', ' ')
            print(f"  冒頭: {preview}...")
        else:
            print("❌ テキスト取得失敗")
    
    print("\n✨ 青空文庫取得テスト完了")

if __name__ == "__main__":
    test_aozora_fetcher() 