#!/usr/bin/env python3
"""
文豪ゆかり地図システム - 完全パイプライン実行スクリプト

全作家の最大作品数での一気通貫実行:
1. データベース初期化・バックアップ
2. 全作家データ収集（最大作品数）
3. 地名抽出・ジオコーディング
4. 全形式エクスポート（CSV、GeoJSON、統計情報）
5. レポート生成

使用方法:
    python scripts/full_pipeline.py [--backup] [--max-works N] [--verbose]
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "core"))
sys.path.insert(0, str(project_root / "src" / "export"))
sys.path.insert(0, str(project_root / "src" / "utils"))

try:
    from collect import BungoDataCollector
    from export_csv import export_db_to_csv
    from export_geojson import GeoJSONExporter
    from db_utils import BungoDatabase
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    print("PYTHONPATH を設定するか、プロジェクトルートから実行してください")
    sys.exit(1)


class FullPipelineExecutor:
    """完全パイプライン実行器"""
    
    # 対象作家（最大網羅）
    MAJOR_AUTHORS = [
        "夏目漱石", "芥川龍之介", "太宰治", "川端康成", "宮沢賢治",
        "森鴎外", "樋口一葉", "石川啄木", "与謝野晶子", "正岡子規",
        "谷崎潤一郎", "三島由紀夫", "志賀直哉", "島崎藤村", "坪内逍遥",
        "泉鏡花", "尾崎紅葉", "幸田露伴", "国木田独歩", "徳冨蘆花"
    ]
    
    def __init__(self, max_works: int = 10, backup: bool = True, verbose: bool = False):
        self.max_works = max_works
        self.backup = backup
        self.verbose = verbose
        self.start_time = datetime.now()
        
        # ログ設定
        log_level = logging.DEBUG if verbose else logging.INFO
        log_filename = f"full_pipeline_{int(time.time())}.log"
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_filename)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🚀 完全パイプライン実行開始: {self.start_time}")
        self.logger.info(f"   対象作家: {len(self.MAJOR_AUTHORS)}名")
        self.logger.info(f"   最大作品数: {max_works}")
        self.logger.info(f"   バックアップ: {backup}")
        
        self.stats = {
            'start_time': self.start_time,
            'phases_completed': [],
            'total_authors': len(self.MAJOR_AUTHORS),
            'successful_authors': 0,
            'total_works': 0,
            'total_places': 0,
            'total_geocoded': 0,
            'export_files': [],
            'errors': []
        }

    def phase1_backup_and_initialize(self) -> bool:
        """フェーズ1: バックアップとデータベース初期化"""
        self.logger.info("📦 フェーズ1: バックアップ・初期化開始")
        
        try:
            if self.backup:
                # バックアップディレクトリ作成
                backup_dir = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.makedirs(backup_dir, exist_ok=True)
                
                # 既存ファイルをバックアップ
                backup_files = [
                    "data/bungo_production.db",
                    "data/geocode_cache.json", 
                    "data/output/bungo_production_export.geojson",
                    "data/output/bungo_stats.json"
                ]
                
                for file_path in backup_files:
                    if os.path.exists(file_path):
                        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                        os.rename(file_path, backup_path)
                        self.logger.info(f"   📁 バックアップ: {file_path} -> {backup_path}")
                
                self.logger.info(f"✅ バックアップ完了: {backup_dir}")
            
            # 古い出力ファイルをアーカイブに移動
            if os.path.exists("data/output"):
                archive_dir = "data/output/archived"
                os.makedirs(archive_dir, exist_ok=True)
                
                for file in os.listdir("data/output"):
                    if file.startswith("bungo_") and file.endswith((".csv", ".geojson", ".json")):
                        if file != "README.md":
                            src = f"data/output/{file}"
                            dst = f"{archive_dir}/{file}"
                            if os.path.exists(src):
                                os.rename(src, dst)
                                self.logger.info(f"   🗂️ アーカイブ: {file}")
            
            self.stats['phases_completed'].append('backup_initialize')
            self.logger.info("✅ フェーズ1完了")
            return True
            
        except Exception as e:
            error_msg = f"❌ フェーズ1エラー: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False

    def phase2_collect_data(self) -> bool:
        """フェーズ2: 全作家データ収集"""
        self.logger.info("📚 フェーズ2: データ収集開始")
        
        try:
            collector = BungoDataCollector("data/bungo_production.db")
            
            # 全作家一括収集
            collection_stats = collector.collect_multiple_authors(
                self.MAJOR_AUTHORS, 
                self.max_works
            )
            
            # 統計更新
            self.stats['successful_authors'] = collection_stats['successful_authors']
            self.stats['total_works'] = collection_stats['total_works']
            self.stats['total_places'] = collection_stats['total_places']
            self.stats['total_geocoded'] = collection_stats['total_geocoded']
            
            # 詳細ログ
            self.logger.info(f"📊 収集結果:")
            self.logger.info(f"   成功作家: {self.stats['successful_authors']}/{self.stats['total_authors']}")
            self.logger.info(f"   総作品数: {self.stats['total_works']}")
            self.logger.info(f"   総地名数: {self.stats['total_places']}")
            self.logger.info(f"   ジオコード: {self.stats['total_geocoded']}")
            
            collector.close()
            
            self.stats['phases_completed'].append('data_collection')
            self.logger.info("✅ フェーズ2完了")
            return True
            
        except Exception as e:
            error_msg = f"❌ フェーズ2エラー: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False

    def phase3_export_all_formats(self) -> bool:
        """フェーズ3: 全形式エクスポート"""
        self.logger.info("📤 フェーズ3: 全形式エクスポート開始")
        
        try:
            db = BungoDatabase("sqlite", "data/bungo_production.db")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. CSV全形式エクスポート
            csv_results = export_db_to_csv(
                db_path="data/bungo_production.db",
                output_dir="data/output",
                export_type="all",
                prefix=f"bungo_export_{timestamp}"
            )
            
            # CSV結果の処理
            for export_type, filepath in csv_results.items():
                self.stats['export_files'].append(filepath)
            self.logger.info(f"✅ CSV エクスポート完了: {len(csv_results)}ファイル")
            
            # 2. GeoJSONエクスポート
            geojson_exporter = GeoJSONExporter("data/output")
            
            geojson_file = geojson_exporter.export_from_database(
                db, f"bungo_production_export_{timestamp}.geojson"
            )
            if geojson_file:
                self.stats['export_files'].append(geojson_file)
                self.logger.info(f"✅ GeoJSON エクスポート完了: {geojson_file}")
            
            # 3. 統計情報エクスポート
            stats_file = geojson_exporter.export_summary_stats(
                db, f"bungo_stats_{timestamp}.json"
            )
            if stats_file:
                self.stats['export_files'].append(stats_file)
                self.logger.info(f"✅ 統計情報エクスポート完了: {stats_file}")
            
            # 4. 分析用CSVエクスポート
            analysis_file = geojson_exporter.export_csv_for_analysis(
                db, f"bungo_analysis_{timestamp}.csv"
            )
            if analysis_file:
                self.stats['export_files'].append(analysis_file)
                self.logger.info(f"✅ 分析用CSV エクスポート完了: {analysis_file}")
            
            db.close()
            
            self.stats['phases_completed'].append('export_all_formats')
            self.logger.info("✅ フェーズ3完了")
            return True
            
        except Exception as e:
            error_msg = f"❌ フェーズ3エラー: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False

    def phase4_generate_report(self) -> bool:
        """フェーズ4: 実行レポート生成"""
        self.logger.info("📋 フェーズ4: レポート生成開始")
        
        try:
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            report = {
                "execution_summary": {
                    "start_time": self.start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "duration_formatted": str(duration),
                    "success": len(self.stats['errors']) == 0
                },
                "pipeline_stats": {
                    "phases_completed": self.stats['phases_completed'],
                    "target_authors": self.stats['total_authors'],
                    "successful_authors": self.stats['successful_authors'],
                    "total_works": self.stats['total_works'],
                    "total_places": self.stats['total_places'],
                    "total_geocoded": self.stats['total_geocoded'],
                    "success_rate": f"{(self.stats['successful_authors']/self.stats['total_authors']*100):.1f}%"
                },
                "export_summary": {
                    "total_files": len(self.stats['export_files']),
                    "files": self.stats['export_files']
                },
                "errors": self.stats['errors']
            }
            
            # レポートファイル出力
            import json
            report_file = f"data/output/pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ レポート生成完了: {report_file}")
            
            # コンソール出力
            print(f"\n🎉 完全パイプライン実行完了！")
            print(f"⏱️  実行時間: {duration}")
            print(f"👥 処理作家: {self.stats['successful_authors']}/{self.stats['total_authors']} ({(self.stats['successful_authors']/self.stats['total_authors']*100):.1f}%)")
            print(f"📚 収集作品: {self.stats['total_works']}作品")
            print(f"🗺️  抽出地名: {self.stats['total_places']}箇所")
            print(f"📍 ジオコード: {self.stats['total_geocoded']}箇所")
            print(f"📁 出力ファイル: {len(self.stats['export_files'])}ファイル")
            print(f"📋 詳細レポート: {report_file}")
            
            if self.stats['errors']:
                print(f"⚠️  エラー: {len(self.stats['errors'])}件")
                for error in self.stats['errors'][:3]:  # 最初の3件のみ表示
                    print(f"   - {error}")
                if len(self.stats['errors']) > 3:
                    print(f"   ...他{len(self.stats['errors'])-3}件")
            
            self.stats['phases_completed'].append('generate_report')
            return True
            
        except Exception as e:
            error_msg = f"❌ フェーズ4エラー: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False

    def execute(self) -> bool:
        """完全パイプライン実行"""
        self.logger.info("🚀🚀🚀 完全パイプライン実行開始 🚀🚀🚀")
        
        phases = [
            ("フェーズ1: バックアップ・初期化", self.phase1_backup_and_initialize),
            ("フェーズ2: データ収集", self.phase2_collect_data),
            ("フェーズ3: 全形式エクスポート", self.phase3_export_all_formats),
            ("フェーズ4: レポート生成", self.phase4_generate_report)
        ]
        
        for phase_name, phase_func in phases:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"開始: {phase_name}")
            self.logger.info(f"{'='*60}")
            
            success = phase_func()
            if not success:
                self.logger.error(f"❌ {phase_name} 失敗 - パイプライン中断")
                return False
            
            self.logger.info(f"✅ {phase_name} 完了")
        
        self.logger.info("\n🎉🎉🎉 完全パイプライン実行成功 🎉🎉🎉")
        return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="文豪ゆかり地図システム - 完全パイプライン実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
実行例:
  # 基本実行（最大10作品/作家）
  python scripts/full_pipeline.py

  # 最大作品数指定
  python scripts/full_pipeline.py --max-works 15

  # バックアップなし・詳細ログ
  python scripts/full_pipeline.py --no-backup --verbose

処理内容:
  1. 既存データのバックアップ
  2. 20名の主要作家からデータ収集
  3. GiNZA地名抽出・ジオコーディング
  4. CSV/GeoJSON/統計情報の全形式エクスポート
  5. 実行レポート生成
        """
    )
    
    parser.add_argument('--max-works', type=int, default=10, 
                       help='作家あたりの最大作品数 (デフォルト: 10)')
    parser.add_argument('--no-backup', action='store_true',
                       help='既存データのバックアップをスキップ')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細ログ出力')
    
    args = parser.parse_args()
    
    try:
        # パイプライン実行器初期化
        executor = FullPipelineExecutor(
            max_works=args.max_works,
            backup=not args.no_backup,
            verbose=args.verbose
        )
        
        # 実行
        success = executor.execute()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ 処理がユーザーによって中断されました")
        return 130
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 