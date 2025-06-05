#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫テキスト取得システム（公式サイト直接アクセス版）
仕様書 bungo_update_spec_draft01.md S2章 青空文庫パイプラインに基づく実装
"""

import requests
import re
import time
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin, quote, unquote
import json
from bs4 import BeautifulSoup
import os

class AozoraFetcherV2:
    """青空文庫テキスト取得クライアント（公式サイト直接アクセス版）"""
    
    def __init__(self, cache_dir: str = "aozora_cache"):
        self.base_url = "https://www.aozora.gr.jp"
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BungoMapSystem/1.0 (Educational Research Purpose)'
        })
        
        # キャッシュディレクトリ作成
        os.makedirs(cache_dir, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        
        # 知名度の高い作品の固定データ（フォールバック用）
        self.famous_works = {
            "夏目漱石": [
                {"title": "坊っちゃん", "file_id": "752", "person_id": "148"},
                {"title": "吾輩は猫である", "file_id": "789", "person_id": "148"},
                {"title": "こころ", "file_id": "773", "person_id": "148"},
                {"title": "三四郎", "file_id": "794", "person_id": "148"},
                {"title": "それから", "file_id": "795", "person_id": "148"}
            ],
            "芥川龍之介": [
                {"title": "羅生門", "file_id": "127", "person_id": "879"},
                {"title": "鼻", "file_id": "42", "person_id": "879"},
                {"title": "蜘蛛の糸", "file_id": "2", "person_id": "879"},
                {"title": "地獄変", "file_id": "128", "person_id": "879"},
                {"title": "藪の中", "file_id": "180", "person_id": "879"}
            ],
            "太宰治": [
                {"title": "人間失格", "file_id": "301", "person_id": "35"},
                {"title": "走れメロス", "file_id": "1567", "person_id": "35"},
                {"title": "津軽", "file_id": "570", "person_id": "35"},
                {"title": "斜陽", "file_id": "1565", "person_id": "35"},
                {"title": "女生徒", "file_id": "1569", "person_id": "35"}
            ]
        }
    
    def search_author_works(self, author_name: str) -> List[Dict]:
        """
        作者名で作品検索（固定データ使用）
        
        Args:
            author_name: 作者名
            
        Returns:
            作品リスト（タイトル、ID、URL等）
        """
        self.logger.info(f"🔍 青空文庫検索: {author_name}")
        
        # 固定データから検索
        if author_name in self.famous_works:
            works = []
            for work_data in self.famous_works[author_name]:
                work_info = {
                    'book_id': work_data['file_id'],
                    'title': work_data['title'],
                    'author': author_name,
                    'person_id': work_data['person_id'],
                    'text_url': f"{self.base_url}/cards/{work_data['person_id']}/files/{work_data['file_id']}_ruby_{work_data['file_id']}.html",
                    'plain_url': f"{self.base_url}/cards/{work_data['person_id']}/files/{work_data['file_id']}.txt",
                    'card_url': f"{self.base_url}/cards/{work_data['person_id']}/card{work_data['file_id']}.html"
                }
                works.append(work_info)
            
            self.logger.info(f"✅ 検索完了: {author_name} - {len(works)}作品発見")
            return works
        else:
            self.logger.warning(f"❌ 固定データに未登録: {author_name}")
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
        plain_url = work_info.get('plain_url')
        
        if not plain_url:
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
            self.logger.info(f"🌐 アクセス中: {plain_url}")
            response = self.session.get(plain_url, timeout=30)
            response.raise_for_status()
            
            # Shift_JISでデコード（青空文庫の標準）
            try:
                text_content = response.content.decode('shift_jis')
            except UnicodeDecodeError:
                # UTF-8でも試行
                try:
                    text_content = response.content.decode('utf-8')
                except UnicodeDecodeError:
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
        # ヘッダー・フッター除去
        lines = raw_text.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            # 本文開始検出
            if not in_content and ('一' in line or 'はじめ' in line or len(line.strip()) > 0 and not line.startswith('---')):
                # ヘッダー情報スキップ後の最初の実質行
                if not (line.startswith('底本：') or line.startswith('入力：') or 
                       line.startswith('校正：') or line.startswith('※') or
                       '---' in line or line.strip() == ''):
                    in_content = True
            
            # フッター検出
            if in_content and ('底本：' in line or '入力：' in line):
                break
            
            if in_content:
                content_lines.append(line)
        
        content = '\n'.join(content_lines)
        
        # 青空文庫記法除去
        patterns = [
            r'［＃.*?］',   # 記法タグ
            r'｜([^《]*?)《.*?》',  # ルビ（読み方は残さず、元の文字のみ）
            r'《.*?》',     # 残ったルビ
            r'〔.*?〕',     # 編者注
            r'※\d+.*?\n',  # 注釈
        ]
        
        cleaned = content
        for pattern in patterns:
            if pattern == r'｜([^《]*?)《.*?》':
                # ルビの場合は元の文字を残す
                cleaned = re.sub(pattern, r'\1', cleaned)
            else:
                cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
        
        # 余分な空白・改行整理
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = re.sub(r'　+', '　', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def get_multiple_works_text(self, author_name: str, max_works: int = 3) -> List[Dict]:
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
                    'plain_text_url': work.get('plain_url', '')
                })
            
            # レート制限（礼儀）
            time.sleep(2)
        
        self.logger.info(f"✅ 複数作品取得完了: {author_name} - {len(results)}作品")
        return results

def test_aozora_fetcher_v2():
    """青空文庫取得テスト（V2）"""
    print("🧪 青空文庫取得テスト（V2）開始")
    
    fetcher = AozoraFetcherV2()
    
    # 夏目漱石作品検索
    print("\n1. 作品検索テスト")
    works = fetcher.search_author_works("夏目漱石")
    print(f"検索結果: {len(works)}作品")
    for work in works[:3]:
        print(f"  - {work['title']} (ID: {work['book_id']})")
        print(f"    URL: {work['plain_url']}")
    
    # テキスト取得テスト
    if works:
        print("\n2. テキスト取得テスト")
        first_work = works[0]  # 坊っちゃん
        text = fetcher.get_text_content(first_work)
        if text:
            print(f"テキスト取得成功: {first_work['title']}")
            print(f"文字数: {len(text)}")
            print(f"冒頭: {text[:200]}...")
            print(f"末尾: ...{text[-200:]}")
        else:
            print("テキスト取得失敗")
    
    # 複数作品取得テスト
    print("\n3. 複数作品取得テスト")
    results = fetcher.get_multiple_works_text("夏目漱石", max_works=2)
    print(f"取得完了: {len(results)}作品")
    for result in results:
        print(f"  - {result['title']}: {result['char_count']}文字")
    
    # 芥川龍之介もテスト
    print("\n4. 芥川龍之介テスト")
    akutagawa_results = fetcher.get_multiple_works_text("芥川龍之介", max_works=1)
    print(f"芥川取得完了: {len(akutagawa_results)}作品")
    for result in akutagawa_results:
        print(f"  - {result['title']}: {result['char_count']}文字")
        print(f"    冒頭: {result['text_content'][:100]}...")
    
    print("✅ テスト完了")

if __name__ == "__main__":
    test_aozora_fetcher_v2() 