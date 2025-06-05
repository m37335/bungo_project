#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫ユーティリティ
仕様書 bungo_update_spec_draft01.md 5章モジュール構成に基づく実装
"""

import requests
import zipfile
import os
import re
import time
import csv
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from urllib.parse import urljoin
import pandas as pd
import io

try:
    from practical_aozora import PracticalAozoraClient
    PRACTICAL_AOZORA_AVAILABLE = True
except ImportError:
    PRACTICAL_AOZORA_AVAILABLE = False


class AozoraUtils:
    """青空文庫ユーティリティクラス"""
    
    def __init__(self, cache_dir: str = "aozora_cache"):
        """
        青空文庫ユーティリティ初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
        """
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
        # キャッシュディレクトリ作成
        Path(cache_dir).mkdir(exist_ok=True)
        
        # 実用青空文庫クライアント初期化（オプション）
        self.practical_client = None
        if PRACTICAL_AOZORA_AVAILABLE:
            try:
                self.practical_client = PracticalAozoraClient(cache_dir=cache_dir)
                self.logger.info("✅ 青空文庫実用クライアント初期化完了")
            except Exception as e:
                self.logger.warning(f"⚠️ 実用クライアント初期化失敗: {e}")
        else:
            self.logger.info("📝 公式APIのみ使用（practical_aozora未インストール）")
        
        # 青空文庫公式URL
        self.base_url = "https://www.aozora.gr.jp"
        self.catalog_url = "https://www.aozora.gr.jp/index_pages/list_person_all_extended_utf8.zip"
    
    def fetch_catalog(self) -> Optional[pd.DataFrame]:
        """
        青空文庫カタログCSVダウンロード
        仕様書 Seq 3: 作品メタ CSV DL
        
        Returns:
            カタログデータフレーム または None
        """
        catalog_file = Path(self.cache_dir) / "aozora_catalog.csv"
        
        # キャッシュ確認（24時間以内）
        if catalog_file.exists():
            file_age = time.time() - catalog_file.stat().st_mtime
            if file_age < 24 * 3600:  # 24時間
                self.logger.info(f"📋 カタログキャッシュ使用: {catalog_file}")
                return pd.read_csv(catalog_file, encoding='utf-8')
        
        try:
            self.logger.info(f"📥 青空文庫カタログダウンロード: {self.catalog_url}")
            
            # ZIPファイルダウンロード
            response = requests.get(self.catalog_url, timeout=30)
            response.raise_for_status()
            
            zip_path = Path(self.cache_dir) / "catalog.zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # ZIP展開
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    csv_file = csv_files[0]
                    zip_ref.extract(csv_file, self.cache_dir)
                    
                    # CSVファイル名を標準化
                    extracted_path = Path(self.cache_dir) / csv_file
                    extracted_path.rename(catalog_file)
            
            # ZIPファイル削除
            zip_path.unlink()
            
            # CSVファイル読み込み
            df = pd.read_csv(catalog_file, encoding='utf-8', dtype=str)
            
            self.logger.info(f"✅ カタログ取得完了: {len(df)}作品")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ カタログ取得エラー: {e}")
            return None
    
    def search_works_in_catalog(self, author_name: str, catalog_df: pd.DataFrame = None) -> List[Dict]:
        """
        カタログから作者の作品を検索
        
        Args:
            author_name: 作者名
            catalog_df: カタログデータフレーム（Noneの場合は自動取得）
            
        Returns:
            作品情報のリスト
        """
        if catalog_df is None:
            catalog_df = self.fetch_catalog()
            if catalog_df is None:
                return []
        
        # 作者名で検索（部分マッチ）
        # フルネームで検索する場合と姓のみで検索する場合の両方をサポート
        if len(author_name) > 2:
            # フルネーム検索（例：夏目漱石）
            author_works = catalog_df[
                (catalog_df['姓'].str.contains(author_name[:2], na=False)) & 
                (catalog_df['名'].str.contains(author_name[2:], na=False))
            ]
            # フルネームでマッチしない場合は姓のみで検索
            if len(author_works) == 0:
                author_works = catalog_df[catalog_df['姓'].str.contains(author_name[:2], na=False)]
        else:
            # 姓のみの検索
            author_works = catalog_df[catalog_df['姓'].str.contains(author_name, na=False)]
        
        works = []
        for _, row in author_works.iterrows():
            work_info = {
                'author_name': f"{row.get('姓', '')}{row.get('名', '')}",
                'title': row.get('作品名', ''),
                'aozora_id': row.get('作品ID', ''),
                'file_url': row.get('XHTML/HTMLファイルURL', ''),
                'text_url': row.get('テキストファイルURL', ''),
                'first_published': row.get('初出', ''),
                'input_date': row.get('入力に使用した版1', '')
            }
            works.append(work_info)
        
        self.logger.info(f"📚 {author_name}の作品: {len(works)}件")
        return works
    
    def download_text(self, work_info: Dict) -> Optional[str]:
        """
        作品テキストダウンロード・正規化
        仕様書 Seq 4: テキスト ZIP DL → Shift-JIS → UTF-8, ルビ・注記・ヘッダ削除
        
        Args:
            work_info: 作品情報辞書
            
        Returns:
            正規化されたテキスト または None
        """
        author = work_info.get('author_name', '')
        title = work_info.get('title', '')
        
        # 実用クライアント優先（一時的に無効化）
        # if self.practical_client:
        #     result = self.practical_client.fetch_work(author, title)
        #     if result and result.get('text'):
        #         text = result['text']
        #         normalized_text = self.normalize_aozora_text(text)
        #         self.logger.info(f"✅ テキスト取得成功（実用クライアント）: {author} - {title}")
        #         return normalized_text
        
        # 公式URLから取得
        text_url = work_info.get('text_url', '')
        if text_url:
            return self._download_from_url(text_url, author, title)
        
        self.logger.warning(f"⚠️ テキスト取得失敗: {author} - {title}")
        return None
    
    def _download_from_url(self, url: str, author: str, title: str) -> Optional[str]:
        """URLからテキストファイルをダウンロード"""
        try:
            self.logger.info(f"📥 テキストダウンロード: {author} - {title}")
            
            # キャッシュ確認
            cache_key = f"{author}_{title}".replace(" ", "_")
            cache_file = Path(self.cache_dir) / f"{cache_key}.txt"
            
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # ダウンロード
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # ZIPファイルかどうかを確認
            if url.endswith('.zip') or response.headers.get('content-type', '').startswith('application/zip'):
                # ZIPファイルの場合
                text = self._extract_text_from_zip(response.content, title)
            else:
                # 通常のテキストファイルの場合
                # Shift-JIS → UTF-8
                try:
                    text = response.content.decode('shift_jis')
                except UnicodeDecodeError:
                    text = response.content.decode('utf-8', errors='ignore')
            
            if not text:
                self.logger.warning(f"⚠️ テキスト抽出失敗: {author} - {title}")
                return None
            
            # 正規化
            normalized_text = self.normalize_aozora_text(text)
            
            # キャッシュ保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(normalized_text)
            
            time.sleep(1)  # API制限対策
            
            self.logger.info(f"✅ テキスト取得完了: {len(normalized_text)}文字")
            return normalized_text
            
        except Exception as e:
            self.logger.error(f"❌ テキストダウンロードエラー: {e}")
            return None
    
    def _extract_text_from_zip(self, zip_data: bytes, title: str) -> Optional[str]:
        """ZIPファイルからテキストファイルを抽出"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                # ZIPファイル内のファイル一覧
                file_list = zip_ref.namelist()
                
                # テキストファイルを探す
                text_file = None
                for filename in file_list:
                    if filename.endswith('.txt'):
                        text_file = filename
                        break
                
                if not text_file:
                    self.logger.warning(f"⚠️ ZIPファイル内にテキストファイルが見つかりません: {file_list}")
                    return None
                
                # テキストファイルを読み込み
                with zip_ref.open(text_file) as f:
                    content = f.read()
                    
                    # Shift-JIS → UTF-8
                    try:
                        text = content.decode('shift_jis')
                    except UnicodeDecodeError:
                        text = content.decode('utf-8', errors='ignore')
                    
                    self.logger.info(f"✅ ZIPからテキスト抽出完了: {text_file}")
                    return text
                    
        except Exception as e:
            self.logger.error(f"❌ ZIP解凍エラー: {e}")
            return None
    
    def normalize_aozora_text(self, text: str) -> str:
        """
        青空文庫テキスト正規化
        ルビ・注記・ヘッダ削除
        
        Args:
            text: 原文テキスト
            
        Returns:
            正規化されたテキスト
        """
        # ヘッダー情報削除（-------...------- で囲まれた部分）
        text = re.sub(r'-{10,}.*?-{10,}', '', text, flags=re.DOTALL)
        
        # ルビ記法削除（｜漢字《かんじ》）
        text = re.sub(r'｜([^《]+)《[^》]+》', r'\1', text)
        text = re.sub(r'([一-龯]+)《[^》]+》', r'\1', text)
        
        # 注記削除（［＃...］）
        text = re.sub(r'［＃[^］]*］', '', text)
        
        # 傍点記法削除（｜文字《・》）
        text = re.sub(r'｜([^《]+)《・+》', r'\1', text)
        
        # 外字注記削除（※）
        text = re.sub(r'※[^、。]*', '', text)
        
        # 改行・空白正規化
        text = re.sub(r'\r\n', '\n', text)  # Windows改行統一
        text = re.sub(r'\s+', ' ', text)    # 連続空白除去
        text = re.sub(r'\n+', '\n', text)   # 連続改行除去
        
        # 青空文庫特有のメタ情報削除
        text = re.sub(r'底本：.*?\n', '', text)
        text = re.sub(r'入力：.*?\n', '', text)
        text = re.sub(r'校正：.*?\n', '', text)
        text = re.sub(r'青空文庫.*?\n', '', text)
        
        return text.strip()
    
    def batch_download_works(self, author_name: str, max_works: int = 5) -> List[Dict]:
        """
        作者の作品を一括ダウンロード
        
        Args:
            author_name: 作者名
            max_works: 最大取得作品数
            
        Returns:
            ダウンロード結果のリスト
        """
        self.logger.info(f"📚 {author_name}の作品一括取得開始（最大{max_works}作品）")
        
        # カタログから作品検索
        catalog_df = self.fetch_catalog()
        if catalog_df is None:
            return []
        
        works = self.search_works_in_catalog(author_name, catalog_df)
        
        # 取得対象を制限
        works = works[:max_works]
        
        results = []
        for work in works:
            text = self.download_text(work)
            
            result = {
                **work,
                'text': text,
                'success': text is not None,
                'text_length': len(text) if text else 0
            }
            results.append(result)
            
            # API制限対策
            time.sleep(2)
        
        success_count = sum(1 for r in results if r['success'])
        self.logger.info(f"✅ 一括取得完了: {success_count}/{len(results)}作品成功")
        
        return results


def test_aozora_utils():
    """青空文庫ユーティリティのテスト"""
    print("🧪 青空文庫ユーティリティ テスト開始")
    
    aozora = AozoraUtils()
    
    # カタログ取得テスト
    print("\n📋 カタログ取得テスト")
    catalog = aozora.fetch_catalog()
    if catalog is not None:
        print(f"   カタログ作品数: {len(catalog)}")
    
    # 作品検索テスト
    print("\n🔍 作品検索テスト")
    works = aozora.search_works_in_catalog("夏目漱石", catalog)
    print(f"   夏目漱石の作品: {len(works)}件")
    
    # テキスト取得テスト
    if works:
        print("\n📥 テキスト取得テスト")
        work = works[0]
        text = aozora.download_text(work)
        if text:
            print(f"   取得成功: {work['title']} ({len(text)}文字)")
        else:
            print(f"   取得失敗: {work['title']}")


if __name__ == "__main__":
    test_aozora_utils() 