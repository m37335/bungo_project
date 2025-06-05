#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
レガシーデータ移行スクリプト
既存の bungo_enhanced_work_places.csv を新しい3テーブル構造に移行

仕様書 bungo_update_spec_draft01.md 8章移行手順に基づく実装
"""

import pandas as pd
import logging
from datetime import datetime
from db_utils import BungoDatabase
from urllib.parse import quote
import os

def migrate_legacy_csv_to_database(csv_file: str = "bungo_enhanced_work_places.csv", 
                                 db_path: str = "bungo_production.db"):
    """
    既存CSVを新データベース構造に移行
    
    Args:
        csv_file: 移行元CSVファイル
        db_path: 移行先データベースパス
    """
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 レガシーデータ移行開始: {csv_file} → {db_path}")
    
    # 既存CSVの確認
    if not os.path.exists(csv_file):
        logger.error(f"❌ CSVファイルが見つかりません: {csv_file}")
        return False
    
    # CSVデータ読み込み
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        logger.info(f"📊 CSVデータ読み込み完了: {len(df)}行")
        print(f"列名: {list(df.columns)}")
    except Exception as e:
        logger.error(f"❌ CSV読み込みエラー: {e}")
        return False
    
    # データベース初期化
    db = BungoDatabase("sqlite", db_path)
    
    # 統計カウンタ
    stats = {
        'authors_added': 0,
        'works_added': 0, 
        'places_added': 0,
        'errors': 0
    }
    
    # 作者リスト抽出・登録
    logger.info("👤 作者データ抽出・登録中...")
    unique_authors = df['author'].unique()
    author_id_map = {}
    
    for author_name in unique_authors:
        try:
            author_id = db.insert_author(author_name)
            author_id_map[author_name] = author_id
            stats['authors_added'] += 1
            logger.info(f"  ✅ 作者登録: {author_name} (ID: {author_id})")
        except Exception as e:
            logger.error(f"  ❌ 作者登録エラー {author_name}: {e}")
            stats['errors'] += 1
    
    # 作品リスト抽出・登録
    logger.info("📚 作品データ抽出・登録中...")
    unique_works = df[['author', 'work_title']].drop_duplicates()
    work_id_map = {}
    
    for _, row in unique_works.iterrows():
        author_name = row['author']
        work_title = row['work_title']
        
        try:
            author_id = author_id_map.get(author_name)
            if author_id:
                work_id = db.insert_work(author_id, work_title)
                work_id_map[(author_name, work_title)] = work_id
                stats['works_added'] += 1
                logger.info(f"  ✅ 作品登録: {author_name} - {work_title} (ID: {work_id})")
            else:
                logger.error(f"  ❌ 作者IDが見つかりません: {author_name}")
                stats['errors'] += 1
        except Exception as e:
            logger.error(f"  ❌ 作品登録エラー {author_name}-{work_title}: {e}")
            stats['errors'] += 1
    
    # 地名データ登録
    logger.info("🗺️ 地名データ登録中...")
    
    for idx, row in df.iterrows():
        try:
            author_name = row['author']
            work_title = row['work_title']
            place_name = row['place_name']
            
            work_id = work_id_map.get((author_name, work_title))
            if not work_id:
                logger.error(f"  ❌ 作品IDが見つかりません: {author_name}-{work_title}")
                stats['errors'] += 1
                continue
            
            # 地名データ変換
            latitude = row.get('latitude')
            longitude = row.get('longitude')
            address = row.get('address', '')
            
            # 文脈データの分割（既存データでは content_excerpt を sentence として使用）
            content_excerpt = row.get('content_excerpt', '')
            text_quote = row.get('text_quote', '')
            
            # before_text, sentence, after_text への分割
            # 簡単な分割（改善の余地あり）
            before_text = ""
            sentence = content_excerpt[:200] if content_excerpt else text_quote[:200] if text_quote else ""
            after_text = ""
            
            # Maps URL作成
            maps_url = f"https://www.google.com/maps/search/{quote(place_name)}"
            
            # 地名登録
            place_id = db.upsert_place(
                work_id=work_id,
                place_name=place_name,
                latitude=latitude if pd.notna(latitude) else None,
                longitude=longitude if pd.notna(longitude) else None,
                address=address,
                before_text=before_text,
                sentence=sentence,
                after_text=after_text,
                extraction_method="legacy_llm",
                confidence=0.8,
                maps_url=maps_url
            )
            
            stats['places_added'] += 1
            
            if idx % 10 == 0:  # 10件ごとに進捗表示
                logger.info(f"  進捗: {idx+1}/{len(df)} ({(idx+1)/len(df)*100:.1f}%)")
                
        except Exception as e:
            logger.error(f"  ❌ 地名登録エラー {idx}: {e}")
            stats['errors'] += 1
    
    # 最終統計
    final_stats = db.get_stats()
    
    logger.info("🎉 移行完了!")
    logger.info(f"📊 移行統計:")
    logger.info(f"  作者: {stats['authors_added']}名追加")
    logger.info(f"  作品: {stats['works_added']}作品追加") 
    logger.info(f"  地名: {stats['places_added']}箇所追加")
    logger.info(f"  エラー: {stats['errors']}件")
    
    logger.info(f"📈 データベース最終状態:")
    logger.info(f"  作者総数: {final_stats['authors_count']}名")
    logger.info(f"  作品総数: {final_stats['works_count']}作品")
    logger.info(f"  地名総数: {final_stats['places_count']}箇所")
    logger.info(f"  ジオコーディング率: {final_stats['geocoded_rate']:.1f}%")
    
    # CSV出力テスト
    export_file = db.export_to_csv("migrated_bungo_data.csv")
    logger.info(f"✅ 移行データCSV出力: {export_file}")
    
    db.close()
    return True

def test_migration():
    """移行テスト（小規模データ）"""
    print("🧪 移行テスト開始")
    
    # テスト用データ作成
    test_data = pd.DataFrame([
        {
            'author': '夏目漱石',
            'work_title': '坊っちゃん', 
            'place_name': '松山市',
            'address': '愛媛県松山市',
            'latitude': 33.8395,
            'longitude': 132.7654,
            'content_excerpt': '四国は松山の中学校に数学の教師として赴任することになった。',
            'text_quote': '親譲りの無鉄砲で小供の時から損ばかりしている。',
            'context': '「坊っちゃん」に登場する松山市',
            'maps_url': 'https://www.google.com/maps/search/松山市',
            'geocoded': True
        },
        {
            'author': '夏目漱石',
            'work_title': '吾輩は猫である',
            'place_name': '本郷',
            'address': '東京都文京区本郷',
            'latitude': 35.7077,
            'longitude': 139.7602,
            'content_excerpt': '東京の本郷あたりの書生の家で飼われることになった。',
            'text_quote': '吾輩は猫である。名前はまだ無い。',
            'context': '「吾輩は猫である」に登場する本郷',
            'maps_url': 'https://www.google.com/maps/search/本郷',
            'geocoded': True
        }
    ])
    
    test_data.to_csv("test_migration_data.csv", index=False, encoding='utf-8')
    
    # 移行実行
    success = migrate_legacy_csv_to_database("test_migration_data.csv", "test_migration.db")
    
    if success:
        print("✅ テスト移行成功")
        
        # 移行結果確認
        db = BungoDatabase("sqlite", "test_migration.db")
        authors = db.search_authors("夏目")
        print(f"移行後作者検索: {len(authors)}件")
        
        places = db.search_places("松山")
        print(f"移行後地名検索: {len(places)}件")
        
        df = db.get_all_places()
        print(f"移行後総データ: {len(df)}件")
        print(df.head())
        
        db.close()
    else:
        print("❌ テスト移行失敗")

if __name__ == "__main__":
    # まずテスト実行
    test_migration()
    
    # 実際のデータ移行（コメントアウト）
    # migrate_legacy_csv_to_database() 