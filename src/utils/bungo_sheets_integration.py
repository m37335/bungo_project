#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪作品地名抽出システム（Google Sheets連携版）
本文引用強化版データをGoogle Sheetsに一覧表として表示・管理

機能:
- 作品内容抜粋 + 本文引用の二重引用システム
- Google Sheetsへの自動アップロード
- 見やすい一覧表形式での表示
- フィルタリング・ソート機能対応
"""

import pandas as pd
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

# Google Sheets APIのインポート（条件付き）
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("ℹ️ Google Sheets APIライブラリが利用できません。")
    print("   pip install gspread google-auth で設定してください。")

from bungo_work_map_enhanced import BungoWorkMapEnhanced

class BungoSheetsIntegration:
    """文豪作品地名抽出システム（Google Sheets連携版）"""
    
    def __init__(self):
        """初期設定"""
        self.enhanced_system = BungoWorkMapEnhanced()
        self.gc = None  # Google Sheets クライアント
        self.sheet_url = None
        
        # ログ設定
        self.setup_logging()
        
        # Google Sheets認証
        self.setup_google_sheets()
    
    def setup_logging(self):
        """ログ設定の初期化"""
        log_filename = f"bungo_sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("📊 文豪作品地名抽出システム（Google Sheets連携版）開始")
    
    def setup_google_sheets(self):
        """Google Sheets API認証設定"""
        if not GSPREAD_AVAILABLE:
            self.logger.warning("⚠️ Google Sheets APIが利用できません")
            return
        
        try:
            # 認証情報ファイルのパス候補
            credentials_paths = [
                "credentials.json",
                "service_account.json",
                os.path.expanduser("~/credentials.json"),
                os.path.expanduser("~/service_account.json")
            ]
            
            credentials_file = None
            for path in credentials_paths:
                if os.path.exists(path):
                    credentials_file = path
                    break
            
            if credentials_file:
                # サービスアカウント認証
                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ]
                
                creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
                self.gc = gspread.authorize(creds)
                self.logger.info(f"✅ Google Sheets API認証完了: {credentials_file}")
            else:
                self.logger.warning("⚠️ 認証情報ファイルが見つかりません")
                self.logger.info("💡 以下のいずれかの場所に認証情報ファイルを配置してください:")
                for path in credentials_paths:
                    self.logger.info(f"   - {path}")
                
        except Exception as e:
            self.logger.error(f"❌ Google Sheets API認証エラー: {e}")
            self.gc = None
    
    def create_enhanced_data(self):
        """本文引用強化版データの生成"""
        self.logger.info("🚀 本文引用強化版データ生成開始")
        
        # 既存のCSVファイルがあるかチェック
        csv_file = "bungo_enhanced_work_places.csv"
        if os.path.exists(csv_file):
            self.logger.info(f"📁 既存データファイル発見: {csv_file}")
            return csv_file
        
        # データ生成
        self.enhanced_system.create_enhanced_integrated_data()
        filename = self.enhanced_system.save_enhanced_data()
        
        return filename
    
    def prepare_sheets_data(self, csv_filename: str) -> List[List]:
        """Google Sheets用データの準備"""
        self.logger.info("📋 Google Sheets用データ準備中...")
        
        # CSVファイル読み込み
        df = pd.read_csv(csv_filename, encoding='utf-8')
        
        # ヘッダー行（日本語）
        headers = [
            "作者",
            "作品タイトル", 
            "地名",
            "住所",
            "緯度",
            "経度",
            "作品内容抜粋",
            "本文引用",
            "文脈説明",
            "Google Maps URL",
            "ジオコーディング成功"
        ]
        
        # データ行の準備
        data_rows = []
        data_rows.append(headers)  # ヘッダー追加
        
        for _, row in df.iterrows():
            data_row = [
                row['author'],
                row['work_title'],
                row['place_name'],
                row['address'],
                str(row['latitude']),
                str(row['longitude']),
                row['content_excerpt'],
                row['text_quote'],
                row['context'],
                row['maps_url'],
                "✅" if row['geocoded'] else "❌"
            ]
            data_rows.append(data_row)
        
        self.logger.info(f"📊 データ準備完了: {len(data_rows)-1}行（ヘッダー除く）")
        return data_rows
    
    def create_google_sheet(self, data_rows: List[List]) -> Optional[str]:
        """Google Sheetsの作成とデータアップロード"""
        if not self.gc:
            self.logger.error("❌ Google Sheets API認証が完了していません")
            return None
        
        try:
            # 新しいスプレッドシート作成
            sheet_title = f"文豪作品地名一覧（本文引用版）_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            self.logger.info(f"📊 Google Sheetsスプレッドシート作成中: {sheet_title}")
            spreadsheet = self.gc.create(sheet_title)
            
            # 最初のワークシート取得
            worksheet = spreadsheet.sheet1
            worksheet.update_title("文豪作品地名データ")
            
            # データをバッチでアップロード
            self.logger.info("📤 データアップロード中...")
            worksheet.update('A1', data_rows)
            
            # ヘッダー行の書式設定
            self.format_header_row(worksheet)
            
            # 列幅の自動調整
            self.auto_resize_columns(worksheet)
            
            # スプレッドシートのURLを取得
            self.sheet_url = spreadsheet.url
            
            # 共有設定（誰でも閲覧可能に設定）
            try:
                spreadsheet.share('', perm_type='anyone', role='reader')
                self.logger.info("🌐 スプレッドシートを誰でも閲覧可能に設定しました")
            except Exception as e:
                self.logger.warning(f"⚠️ 共有設定エラー: {e}")
            
            self.logger.info(f"✅ Google Sheetsアップロード完了")
            self.logger.info(f"🔗 URL: {self.sheet_url}")
            
            return self.sheet_url
            
        except Exception as e:
            self.logger.error(f"❌ Google Sheetsアップロードエラー: {e}")
            return None
    
    def format_header_row(self, worksheet):
        """ヘッダー行の書式設定"""
        try:
            # ヘッダー行を太字にする
            worksheet.format('A1:K1', {
                "textFormat": {
                    "bold": True,
                    "fontSize": 12
                },
                "backgroundColor": {
                    "red": 0.8,
                    "green": 0.9,
                    "blue": 1.0
                }
            })
            self.logger.info("✨ ヘッダー行の書式設定完了")
        except Exception as e:
            self.logger.warning(f"⚠️ ヘッダー書式設定エラー: {e}")
    
    def auto_resize_columns(self, worksheet):
        """列幅の自動調整"""
        try:
            # 各列の適切な幅を設定
            column_widths = {
                'A': 100,  # 作者
                'B': 150,  # 作品タイトル
                'C': 120,  # 地名
                'D': 200,  # 住所
                'E': 100,  # 緯度
                'F': 100,  # 経度
                'G': 300,  # 作品内容抜粋
                'H': 300,  # 本文引用
                'I': 150,  # 文脈説明
                'J': 200,  # Google Maps URL
                'K': 80    # ジオコーディング成功
            }
            
            for column, width in column_widths.items():
                worksheet.update_dimension_group_size(
                    'COLUMNS',
                    column,
                    column,
                    width
                )
            
            self.logger.info("📏 列幅自動調整完了")
        except Exception as e:
            self.logger.warning(f"⚠️ 列幅調整エラー: {e}")
    
    def add_summary_sheet(self, spreadsheet):
        """統計サマリーシートの追加"""
        try:
            # 新しいワークシート追加
            summary_sheet = spreadsheet.add_worksheet("統計サマリー", rows=20, cols=5)
            
            # CSVデータ読み込み
            df = pd.read_csv("bungo_enhanced_work_places.csv")
            
            # 統計データ作成
            summary_data = [
                ["項目", "値", "", "", ""],
                ["総データ件数", len(df), "", "", ""],
                ["文豪数", df['author'].nunique(), "", "", ""],
                ["作品数", df['work_title'].nunique(), "", "", ""],
                ["地名数", df['place_name'].nunique(), "", "", ""],
                ["ジオコーディング成功率", f"{(df['geocoded'].sum() / len(df) * 100):.1f}%", "", "", ""],
                ["", "", "", "", ""],
                ["文豪別データ数", "", "", "", ""],
            ]
            
            # 文豪別統計追加
            author_counts = df.groupby('author').size()
            for author, count in author_counts.items():
                summary_data.append([author, f"{count}件", "", "", ""])
            
            # データアップロード
            summary_sheet.update('A1', summary_data)
            
            # ヘッダー書式設定
            summary_sheet.format('A1:E1', {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            
            self.logger.info("📈 統計サマリーシート追加完了")
            
        except Exception as e:
            self.logger.warning(f"⚠️ サマリーシート追加エラー: {e}")
    
    def create_demo_sheets_without_auth(self):
        """認証なしでのデモ用CSV生成"""
        self.logger.info("📝 認証なしデモ用データ生成")
        
        # データ生成
        csv_filename = self.create_enhanced_data()
        
        # 見やすいCSV形式で出力
        df = pd.read_csv(csv_filename)
        
        # 日本語ヘッダー版CSV作成
        df_japanese = df.copy()
        df_japanese.columns = [
            "作者", "作品タイトル", "地名", "住所", "緯度", "経度",
            "作品内容抜粋", "本文引用", "文脈説明", "Google_Maps_URL", "ジオコーディング成功"
        ]
        
        japanese_filename = "bungo_enhanced_japanese.csv"
        df_japanese.to_csv(japanese_filename, index=False, encoding='utf-8')
        
        self.logger.info(f"📁 日本語ヘッダー版CSV保存: {japanese_filename}")
        
        # 統計情報出力
        self.print_data_statistics(df)
        
        return japanese_filename
    
    def print_data_statistics(self, df):
        """データ統計情報の表示"""
        print(f"\n📊 文豪作品地名データ統計")
        print(f"=" * 50)
        print(f"📈 総データ件数: {len(df)}件")
        print(f"👤 文豪数: {df['author'].nunique()}名")
        print(f"📚 作品数: {df['work_title'].nunique()}作品")
        print(f"🗺️ 地名数: {df['place_name'].nunique()}箇所")
        print(f"✅ ジオコーディング成功率: {(df['geocoded'].sum() / len(df) * 100):.1f}%")
        
        print(f"\n👤 文豪別データ数:")
        author_counts = df.groupby('author').size().sort_values(ascending=False)
        for author, count in author_counts.items():
            print(f"   {author}: {count}件")
        
        print(f"\n📚 主要作品別データ数:")
        work_counts = df.groupby('work_title').size().sort_values(ascending=False).head(10)
        for work, count in work_counts.items():
            print(f"   {work}: {count}件")
        
        print(f"\n✨ データ構造:")
        print(f"   ・作品内容抜粋: 地名が登場する文章")
        print(f"   ・本文引用: 作品の印象的な一節")
        print(f"   ・二重引用システムで豊富な情報を提供")
    
    def run_full_integration(self):
        """完全なGoogle Sheets連携処理"""
        self.logger.info("🚀 Google Sheets連携処理開始")
        
        try:
            # 1. データ生成
            csv_filename = self.create_enhanced_data()
            
            # 2. Google Sheets用データ準備
            data_rows = self.prepare_sheets_data(csv_filename)
            
            # 3. Google Sheetsアップロード
            if self.gc:
                sheet_url = self.create_google_sheet(data_rows)
                
                if sheet_url:
                    print(f"\n🎉 Google Sheets連携完了！")
                    print(f"🔗 スプレッドシートURL: {sheet_url}")
                    print(f"📊 一覧表として閲覧・編集可能です")
                    return sheet_url
                else:
                    self.logger.error("❌ Google Sheetsアップロード失敗")
            else:
                # 認証なしの場合はCSV生成のみ
                demo_filename = self.create_demo_sheets_without_auth()
                print(f"\n📝 認証なしデモ版完了！")
                print(f"📁 ファイル: {demo_filename}")
                print(f"💡 Google Sheets連携するには認証情報を設定してください")
                return demo_filename
                
        except Exception as e:
            self.logger.error(f"❌ 処理エラー: {e}")
            return None

def main():
    """メイン処理"""
    print("📊 文豪作品地名抽出システム（Google Sheets連携版）")
    print("=" * 70)
    print("✨ 本文引用強化版データをGoogle Sheetsで一覧表示")
    print()
    
    integration = BungoSheetsIntegration()
    
    try:
        result = integration.run_full_integration()
        
        if result:
            print(f"\n🎉 処理完了！")
            if result.startswith('http'):
                print(f"🌐 Google Sheets: {result}")
                print(f"📱 モバイルでも閲覧可能")
                print(f"🔍 フィルタリング・ソート機能使用可能")
            else:
                print(f"📁 ローカルファイル: {result}")
                print(f"💻 Excelやスプレッドシートアプリで開けます")
        else:
            print(f"\n❌ 処理に失敗しました")
            
    except KeyboardInterrupt:
        print("\n⏹️ 処理を中断しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main() 