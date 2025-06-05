#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫実用クライアント
仕様書 bungo_update_spec_draft01.md S2章 青空文庫パイプラインに基づく実装

実際の青空文庫HTMLページからスクレイピングでテキストを取得
"""

import requests
import re
import time
import os
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AozoraPracticalClient:
    """青空文庫実用クライアント（HTML解析版）"""
    
    def __init__(self, cache_dir: str = "aozora_cache"):
        self.base_url = "https://www.aozora.gr.jp"
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (BungoMapSystem/1.0) Educational Research'
        })
        
        # キャッシュディレクトリ作成
        os.makedirs(cache_dir, exist_ok=True)
        
        # 既知の作品ID辞書（手動キュレーション）
        self.known_works = {
            '夏目漱石': {
                '坊っちゃん': ('000148', 'files/752_14964.html'),
                '吾輩は猫である': ('000148', 'files/789_14547.html'),
                'こころ': ('000148', 'files/773_14560.html'),
                '三四郎': ('000148', 'files/794_14972.html'),
                'それから': ('000148', 'files/795_15005.html')
            },
            '芥川龍之介': {
                '羅生門': ('000879', 'files/127_15260.html'),
                '蜘蛛の糸': ('000879', 'files/92_2689.html'),
                '鼻': ('000879', 'files/42_375.html'),
                '地獄変': ('000879', 'files/1869_6257.html')
            },
            '太宰治': {
                '人間失格': ('000035', 'files/301_14912.html'),
                '走れメロス': ('000035', 'files/1567_4948.html'),
                '津軽': ('000035', 'files/570_8243.html')
            },
            '川端康成': {
                '雪国': ('000084', 'files/1235_8303.html'),
                '伊豆の踊子': ('000084', 'files/45_362.html')
            },
            '宮沢賢治': {
                '銀河鉄道の夜': ('000081', 'files/456_15050.html'),
                '注文の多い料理店': ('000081', 'files/1927_6925.html'),
                'セロ弾きのゴーシュ': ('000081', 'files/470_15407.html')
            }
        }
    
    def get_work_url(self, author: str, title: str) -> Optional[str]:
        """既知作品のURL取得"""
        if author in self.known_works and title in self.known_works[author]:
            author_id, file_path = self.known_works[author][title]
            url = f"{self.base_url}/cards/{author_id}/{file_path}"
            return url
        return None
    
    def fetch_text_from_html(self, url: str) -> Optional[str]:
        """HTMLページからテキスト抽出"""
        try:
            self.logger.info(f"HTMLテキスト取得: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                self.logger.warning(f"HTTP取得失敗: {response.status_code}")
                return None
            
            # Shift_JISでデコード（青空文庫のデフォルト）
            try:
                html_content = response.content.decode('shift_jis')
            except UnicodeDecodeError:
                html_content = response.content.decode('utf-8', errors='ignore')
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 本文抽出（青空文庫HTML構造に基づく）
            # main_textクラスまたはdiv.main_textを探す
            main_text = soup.find('div', class_='main_text')
            if not main_text:
                # bodyの中から本文らしい部分を抽出
                body = soup.find('body')
                if body:
                    # scriptとstyleタグを除去
                    for tag in body(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    main_text = body
            
            if main_text:
                # テキスト抽出とクリーニング
                text = main_text.get_text()
                # 青空文庫特有の注記を除去
                text = re.sub(r'［＃[^］]*］', '', text)  # ルビ等の注記除去
                text = re.sub(r'\s+', ' ', text)  # 空白正規化
                text = text.strip()
                
                self.logger.info(f"テキスト抽出成功: {len(text)}文字")
                return text
            else:
                self.logger.warning("本文が見つかりません")
                return None
                
        except Exception as e:
            self.logger.error(f"テキスト取得エラー: {e}")
            return None
    
    def cache_text(self, cache_key: str, text: str) -> str:
        """テキストキャッシュ保存"""
        cache_file = Path(self.cache_dir) / f"{cache_key}.txt"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(text)
            self.logger.info(f"キャッシュ保存: {cache_file}")
            return str(cache_file)
        except Exception as e:
            self.logger.error(f"キャッシュ保存エラー: {e}")
            return ""
    
    def load_cached_text(self, cache_key: str) -> Optional[str]:
        """キャッシュからテキスト読み込み"""
        cache_file = Path(self.cache_dir) / f"{cache_key}.txt"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                self.logger.info(f"キャッシュ読み込み: {cache_file}")
                return text
            except Exception as e:
                self.logger.error(f"キャッシュ読み込みエラー: {e}")
        return None
    
    def fetch_work(self, author: str, title: str) -> Optional[Dict]:
        """作品取得（キャッシュ機能付き）"""
        cache_key = f"{author}_{title}".replace(" ", "_")
        
        # キャッシュ確認
        cached_text = self.load_cached_text(cache_key)
        if cached_text:
            return {
                'author': author,
                'title': title,
                'text': cached_text,
                'cache_hit': True,
                'source': 'cache'
            }
        
        # URLを取得
        url = self.get_work_url(author, title)
        if not url:
            self.logger.warning(f"未対応作品: {author} - {title}")
            return None
        
        # テキスト取得
        text = self.fetch_text_from_html(url)
        if text:
            # キャッシュ保存
            self.cache_text(cache_key, text)
            time.sleep(2)  # サイト負荷軽減
            
            return {
                'author': author,
                'title': title,
                'text': text,
                'cache_hit': False,
                'source': 'web',
                'url': url
            }
        
        return None
    
    def list_available_works(self) -> Dict[str, List[str]]:
        """利用可能作品リスト"""
        return {author: list(works.keys()) for author, works in self.known_works.items()}

def test_practical_client():
    """実用青空文庫クライアントテスト"""
    print("🧪 青空文庫実用クライアント テスト開始")
    
    client = AozoraPracticalClient()
    
    # 利用可能作品表示
    print("\n📚 利用可能作品一覧:")
    available = client.list_available_works()
    for author, works in available.items():
        print(f"  {author}: {', '.join(works[:3])}{'...' if len(works) > 3 else ''}")
    
    # テストケース1: 坊っちゃん取得
    print("\n📖 テスト1: 夏目漱石『坊っちゃん』取得")
    work = client.fetch_work("夏目漱石", "坊っちゃん")
    if work:
        text = work['text']
        print(f"✅ 取得成功: {work['title']} ({len(text)}文字)")
        print(f"📁 キャッシュ: {'ヒット' if work['cache_hit'] else 'ミス'}")
        print(f"🌐 ソース: {work['source']}")
        print(f"📝 冒頭: {text[:150]}...")
    else:
        print("❌ 取得失敗")
    
    # テストケース2: 羅生門取得
    print("\n📖 テスト2: 芥川龍之介『羅生門』取得")
    work = client.fetch_work("芥川龍之介", "羅生門")
    if work:
        text = work['text']
        print(f"✅ 取得成功: {work['title']} ({len(text)}文字)")
        print(f"📁 キャッシュ: {'ヒット' if work['cache_hit'] else 'ミス'}")
        print(f"📝 冒頭: {text[:150]}...")
    else:
        print("❌ 取得失敗")
    
    print("\n🎯 青空文庫実用クライアント テスト完了")

if __name__ == "__main__":
    test_practical_client() 