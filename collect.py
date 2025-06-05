#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪地図システム データ収集パイプライン
仕様書 bungo_update_spec_draft01.md 4章データ取得・更新フローに基づく実装
"""

import argparse
import logging
import sys
import time
from typing import List, Dict, Optional

# ローカルモジュールインポート
try:
    from db_utils import BungoDatabase
    from aozora_utils import AozoraUtils
    from aozora_place_extract import AozoraPlaceExtractor
    from geocode_utils import GeocodeUtils
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    print("必要なモジュールをインストールしてください: pip install -r requirements.txt")
    sys.exit(1)


class BungoDataCollector:
    """文豪データ収集パイプライン"""
    
    def __init__(self, db_path: str = "bungo_production.db"):
        self.logger = logging.getLogger(__name__)
        
        # データベース初期化
        self.db = BungoDatabase("sqlite", db_path)
        
        # 青空文庫ユーティリティ
        self.aozora = AozoraUtils()
        
        # 地名抽出器
        self.place_extractor = AozoraPlaceExtractor()
        
        # ジオコーダー
        self.geocoder = GeocodeUtils()
        
        self.logger.info(f"✅ データ収集パイプライン初期化完了: {db_path}")
    
    def collect_author_data(self, author_name: str, max_works: int = 5, geocode: bool = True) -> Dict:
        """
        作者のデータを一括収集
        仕様書 Seq 1-7: Wikipedia→works → 青空文庫→places → ジオコード
        
        Args:
            author_name: 作者名
            max_works: 最大取得作品数
            geocode: ジオコーディング実行フラグ
            
        Returns:
            収集結果統計
        """
        self.logger.info(f"📚 {author_name}のデータ収集開始")
        
        stats = {
            'author_name': author_name,
            'authors_inserted': 0,
            'works_inserted': 0,
            'places_inserted': 0,
            'geocoded_count': 0,
            'errors': []
        }
        
        try:
            # Step 1: 作者登録
            author_id = self.db.insert_author(author_name)
            if author_id:
                stats['authors_inserted'] = 1
                self.logger.info(f"✅ 作者登録: {author_name} (ID: {author_id})")
            
            # Step 2-4: 青空文庫から作品取得
            self.logger.info("📥 青空文庫から作品取得中...")
            work_results = self.aozora.batch_download_works(author_name, max_works)
            
            # Step 2: 作品データベース登録
            for work_result in work_results:
                if work_result.get('success'):
                    work_id = self.db.insert_work(
                        author_id=author_id,
                        title=work_result['title'],
                        aozora_url=work_result.get('file_url'),
                        publication_year=None,  # 青空文庫からは取得困難
                        genre=None
                    )
                    if work_id:
                        stats['works_inserted'] += 1
                        work_result['work_id'] = work_id
            
            # Step 5: GiNZA地名抽出
            self.logger.info("🗺️ GiNZA地名抽出中...")
            all_places = self.place_extractor.batch_extract_from_works(work_results)
            
            # Step 6: 地名データベース登録
            for place_data in all_places:
                work_id = self._find_work_id(place_data, work_results)
                if work_id:
                    place_id = self.db.upsert_place(
                        work_id=work_id,
                        place_name=place_data['place_name'],
                        before_text=place_data.get('before_text', ''),
                        sentence=place_data.get('sentence', ''),
                        after_text=place_data.get('after_text', ''),
                        extraction_method=place_data.get('extraction_method', 'ginza'),
                        confidence=place_data.get('confidence', 0.8)
                    )
                    if place_id:
                        stats['places_inserted'] += 1
            
            # Step 7: ジオコーディング（オプション）
            if geocode and stats['places_inserted'] > 0:
                self.logger.info("📍 ジオコーディング実行中...")
                geocode_stats = self.geocoder.update_database_places(self.db)
                stats['geocoded_count'] = geocode_stats.get('updated', 0)
            
            self.logger.info(f"✅ {author_name}のデータ収集完了")
            
        except Exception as e:
            error_msg = f"❌ データ収集エラー: {e}"
            self.logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        return stats
    
    def _find_work_id(self, place_data: Dict, work_results: List[Dict]) -> Optional[int]:
        """地名データから対応する作品IDを検索"""
        author_name = place_data.get('author_name', '')
        work_title = place_data.get('work_title', '')
        
        for work_result in work_results:
            if (work_result.get('author_name') == author_name and 
                work_result.get('title') == work_title and
                work_result.get('work_id')):
                return work_result['work_id']
        
        return None
    
    def collect_multiple_authors(self, author_names: List[str], max_works: int = 5) -> Dict:
        """
        複数作者のデータを一括収集
        
        Args:
            author_names: 作者名リスト
            max_works: 作者あたりの最大作品数
            
        Returns:
            全体の収集結果統計
        """
        self.logger.info(f"📚 複数作者データ収集開始: {len(author_names)}名")
        
        overall_stats = {
            'total_authors': len(author_names),
            'successful_authors': 0,
            'total_works': 0,
            'total_places': 0,
            'total_geocoded': 0,
            'author_details': []
        }
        
        for i, author_name in enumerate(author_names, 1):
            self.logger.info(f"== 処理中 ({i}/{len(author_names)}): {author_name} ==")
            
            author_stats = self.collect_author_data(author_name, max_works, geocode=False)
            overall_stats['author_details'].append(author_stats)
            
            if not author_stats['errors']:
                overall_stats['successful_authors'] += 1
            
            overall_stats['total_works'] += author_stats['works_inserted']
            overall_stats['total_places'] += author_stats['places_inserted']
            
            # API制限対策
            time.sleep(3)
        
        # 最後に一括ジオコーディング
        if overall_stats['total_places'] > 0:
            self.logger.info("📍 一括ジオコーディング実行中...")
            geocode_stats = self.geocoder.update_database_places(self.db)
            overall_stats['total_geocoded'] = geocode_stats.get('updated', 0)
        
        self.logger.info("✅ 複数作者データ収集完了")
        return overall_stats
    
    def test_pipeline(self) -> bool:
        """データ収集パイプラインのテスト"""
        self.logger.info("🧪 データ収集パイプライン テスト開始")
        
        # 小規模テスト
        test_stats = self.collect_author_data("夏目漱石", max_works=1, geocode=True)
        
        success = (
            test_stats['authors_inserted'] > 0 and
            test_stats['works_inserted'] > 0 and 
            len(test_stats['errors']) == 0
        )
        
        if success:
            self.logger.info("✅ パイプラインテスト成功")
        else:
            self.logger.error("❌ パイプラインテスト失敗")
        
        return success
    
    def close(self):
        """リソースクリーンアップ"""
        self.db.close()


def main():
    """メインCLI関数"""
    parser = argparse.ArgumentParser(
        description='文豪地図システム データ収集パイプライン',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一作者の作品収集
  python collect.py --author "夏目漱石" --max-works 3

  # 複数作者の一括収集
  python collect.py --all --max-works 5

  # パイプラインテスト
  python collect.py --test

主要機能:
  1. Wikipedia/青空文庫から作品テキスト取得
  2. GiNZA NERによる地名抽出（前後文付き）
  3. データベース登録・ジオコーディング
        """
    )
    
    parser.add_argument('--author', help='作者名を指定')
    parser.add_argument('--all', action='store_true', help='主要作家全員を収集')
    parser.add_argument('--max-works', type=int, default=5, help='最大取得作品数')
    parser.add_argument('--db-path', default='bungo_production.db', help='データベースパス')
    parser.add_argument('--no-geocode', action='store_true', help='ジオコーディングをスキップ')
    parser.add_argument('--test', action='store_true', help='テストモード実行')
    parser.add_argument('--title', help='特定の作品タイトルを指定')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細ログ出力')
    
    args = parser.parse_args()
    
    # ログ設定
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'collect_{int(time.time())}.log')
        ]
    )
    
    # データ収集器初期化
    try:
        collector = BungoDataCollector(args.db_path)
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return 1
    
    try:
        if args.test:
            # パイプラインテスト
            success = collector.test_pipeline()
            return 0 if success else 1
        
        elif args.author:
            # 単一作者収集
            stats = collector.collect_author_data(
                args.author, 
                args.max_works, 
                geocode=not args.no_geocode
            )
            
            print(f"\n📊 収集結果: {args.author}")
            print(f"   作者登録: {stats['authors_inserted']}")
            print(f"   作品登録: {stats['works_inserted']}")
            print(f"   地名登録: {stats['places_inserted']}")
            print(f"   ジオコード: {stats['geocoded_count']}")
            
            if stats['errors']:
                print(f"   エラー: {len(stats['errors'])}件")
                for error in stats['errors']:
                    print(f"     - {error}")
        
        elif args.all:
            # 複数作者一括収集
            major_authors = [
                "夏目漱石", "芥川龍之介", "太宰治", "川端康成", "宮沢賢治",
                "森鴎外", "樋口一葉", "石川啄木", "与謝野晶子", "正岡子規"
            ]
            
            stats = collector.collect_multiple_authors(major_authors, args.max_works)
            
            print(f"\n📊 一括収集結果:")
            print(f"   対象作者: {stats['total_authors']}名")
            print(f"   成功作者: {stats['successful_authors']}名")
            print(f"   総作品数: {stats['total_works']}")
            print(f"   総地名数: {stats['total_places']}")
            print(f"   ジオコード: {stats['total_geocoded']}")
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️ 処理がユーザーによって中断されました")
        return 130
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        collector.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 