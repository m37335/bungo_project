#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoJSONエクスポートユーティリティ
仕様書 bungo_update_spec_draft01.md 5章モジュール構成に基づく実装
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class GeoJSONExporter:
    """GeoJSONエクスポートユーティリティ"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Args:
            output_dir: 出力ディレクトリ
        """
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # 出力ディレクトリ作成
        os.makedirs(output_dir, exist_ok=True)
    
    def export_from_database(self, db, output_filename: str = "bungo_places.geojson") -> str:
        """
        データベースからGeoJSONファイルを生成
        
        Args:
            db: BungoDatabaseインスタンス
            output_filename: 出力ファイル名
            
        Returns:
            出力ファイルパス
        """
        # データベースから全地名データを取得
        df = self._get_places_dataframe(db)
        
        if df.empty:
            self.logger.warning("⚠️ 地名データが見つかりません")
            return None
        
        # GeoJSON生成
        geojson = self._create_geojson(df)
        
        # ファイル出力
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        # 統計情報ログ
        total_places = len(df)
        geocoded_places = len(df[df['latitude'].notna() & df['longitude'].notna()])
        geocoded_rate = geocoded_places / total_places * 100 if total_places > 0 else 0
        
        self.logger.info(f"✅ GeoJSONエクスポート完了: {output_path}")
        self.logger.info(f"   総地名数: {total_places}")
        self.logger.info(f"   ジオコーディング済み: {geocoded_places} ({geocoded_rate:.1f}%)")
        
        return output_path
    
    def _get_places_dataframe(self, db) -> pd.DataFrame:
        """データベースから地名データフレームを取得"""
        if hasattr(db, 'conn'):  # SQLite
            query = """
            SELECT 
                p.place_id,
                p.work_id,
                p.place_name,
                p.latitude,
                p.longitude,
                p.address,
                p.before_text,
                p.sentence,
                p.after_text,
                p.extraction_method,
                p.confidence,
                p.maps_url,
                p.geocoded,
                w.title as work_title,
                w.aozora_url,
                w.wikipedia_url as work_wikipedia_url,
                a.name as author_name,
                a.wikipedia_url as author_wikipedia_url
            FROM places p
            JOIN works w ON p.work_id = w.work_id
            JOIN authors a ON w.author_id = a.author_id
            WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
            ORDER BY a.name, w.title, p.place_name
            """
            return pd.read_sql_query(query, db.conn)
        else:
            raise NotImplementedError("Google SheetsからのGeoJSONエクスポートは未実装")
    
    def _create_geojson(self, df: pd.DataFrame) -> Dict:
        """データフレームからGeoJSON形式を生成"""
        features = []
        
        for _, row in df.iterrows():
            # MapKit用のプロパティ設計
            properties = {
                # 基本情報
                "place_id": int(row['place_id']) if pd.notna(row['place_id']) else None,
                "place_name": row['place_name'],
                "author_name": row['author_name'],
                "work_title": row['work_title'],
                
                # 地理情報
                "address": row['address'] if pd.notna(row['address']) else None,
                "maps_url": row['maps_url'] if pd.notna(row['maps_url']) else None,
                
                # 文脈情報（MapKit アノテーション用）
                "before_text": row['before_text'] if pd.notna(row['before_text']) else "",
                "sentence": row['sentence'] if pd.notna(row['sentence']) else "",
                "after_text": row['after_text'] if pd.notna(row['after_text']) else "",
                "context": self._create_context_text(row),
                
                # メタデータ
                "extraction_method": row['extraction_method'] if pd.notna(row['extraction_method']) else "unknown",
                "confidence": float(row['confidence']) if pd.notna(row['confidence']) else 0.0,
                "aozora_url": row['aozora_url'] if pd.notna(row['aozora_url']) else None,
                "work_wikipedia_url": row['work_wikipedia_url'] if pd.notna(row['work_wikipedia_url']) else None,
                "author_wikipedia_url": row['author_wikipedia_url'] if pd.notna(row['author_wikipedia_url']) else None,
                
                # 表示用情報
                "title": f"{row['author_name']}『{row['work_title']}』",
                "subtitle": row['place_name'],
                "description": self._create_description(row)
            }
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['longitude']), float(row['latitude'])]  # GeoJSONは [lng, lat] 順
                },
                "properties": properties
            }
            
            features.append(feature)
        
        # GeoJSON構造
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "generator": "bungo_places_exporter",
                "generated_at": datetime.now().isoformat(),
                "total_features": len(features),
                "authors": df['author_name'].nunique(),
                "works": df['work_title'].nunique(),
                "places": df['place_name'].nunique()
            },
            "features": features
        }
        
        return geojson
    
    def _create_context_text(self, row) -> str:
        """前後文を組み合わせた文脈テキストを作成"""
        parts = []
        
        if pd.notna(row['before_text']) and row['before_text'].strip():
            parts.append(row['before_text'].strip())
        
        if pd.notna(row['sentence']) and row['sentence'].strip():
            parts.append(f"【{row['sentence'].strip()}】")  # メイン文を強調
        
        if pd.notna(row['after_text']) and row['after_text'].strip():
            parts.append(row['after_text'].strip())
        
        return "".join(parts) if parts else ""
    
    def _create_description(self, row) -> str:
        """MapKit アノテーション用の説明文を作成"""
        desc_parts = []
        
        # 作品情報
        desc_parts.append(f"📚 {row['author_name']}『{row['work_title']}』")
        
        # 住所情報
        if pd.notna(row['address']):
            desc_parts.append(f"📍 {row['address']}")
        
        # 文脈情報（簡略版）
        context = self._create_context_text(row)
        if context and len(context) > 0:
            # 長すぎる場合は省略
            if len(context) > 100:
                context = context[:97] + "..."
            desc_parts.append(f"💭 {context}")
        
        # 信頼度情報
        if pd.notna(row['confidence']) and row['confidence'] > 0:
            desc_parts.append(f"🎯 信頼度: {row['confidence']:.1f}")
        
        return "\n".join(desc_parts)
    
    def export_summary_stats(self, db, output_filename: str = "bungo_stats.json") -> str:
        """
        統計情報をJSONで出力
        
        Args:
            db: BungoDatabaseインスタンス
            output_filename: 出力ファイル名
            
        Returns:
            出力ファイルパス
        """
        # データベース統計取得
        stats = db.get_stats()
        
        # 追加統計情報
        df = self._get_places_dataframe(db)
        
        extended_stats = {
            **stats,
            "export_stats": {
                "exportable_places": len(df),
                "top_authors": df['author_name'].value_counts().head(10).to_dict(),
                "top_places": df['place_name'].value_counts().head(10).to_dict(),
                "extraction_methods": df['extraction_method'].value_counts().to_dict(),
                "confidence_distribution": {
                    "high (>0.8)": len(df[df['confidence'] > 0.8]),
                    "medium (0.5-0.8)": len(df[(df['confidence'] >= 0.5) & (df['confidence'] <= 0.8)]),
                    "low (<0.5)": len(df[df['confidence'] < 0.5])
                }
            },
            "generated_at": datetime.now().isoformat()
        }
        
        # ファイル出力
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(extended_stats, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ 統計情報エクスポート完了: {output_path}")
        
        return output_path
    
    def export_csv_for_analysis(self, db, output_filename: str = "bungo_analysis.csv") -> str:
        """
        分析用CSVファイルを出力
        
        Args:
            db: BungoDatabaseインスタンス
            output_filename: 出力ファイル名
            
        Returns:
            出力ファイルパス
        """
        df = self._get_places_dataframe(db)
        
        if df.empty:
            self.logger.warning("⚠️ エクスポート可能なデータがありません")
            return None
        
        # 分析用に列を整理（存在する列のみ使用）
        available_cols = ['author_name', 'work_title', 'place_name', 'latitude', 'longitude', 
                         'address', 'extraction_method', 'confidence']
        analysis_df = df[[col for col in available_cols if col in df.columns]].copy()
        
        # 文脈列を追加
        analysis_df['context'] = df.apply(self._create_context_text, axis=1)
        
        output_path = os.path.join(self.output_dir, output_filename)
        analysis_df.to_csv(output_path, index=False, encoding='utf-8')
        
        self.logger.info(f"✅ 分析用CSVエクスポート完了: {output_path}")
        self.logger.info(f"   データ行数: {len(analysis_df)}")
        
        return output_path


def test_geojson_exporter():
    """GeoJSONエクスポーターのテスト"""
    from db_utils import BungoDatabase
    
    # テスト用データベース
    db = BungoDatabase("sqlite", "test_export.db")
    
    # テストデータ挿入
    author_id = db.insert_author("テスト作家", "https://example.com")
    work_id = db.insert_work(author_id, "テスト作品", "https://example.com")
    
    db.upsert_place(work_id, "東京都", 35.6762, 139.6503, "東京都, 日本", 
                   "前文", "本文に東京都が登場", "後文", "test", 0.9)
    db.upsert_place(work_id, "大阪府", 34.6937, 135.5023, "大阪府, 日本", 
                   "前文", "大阪府の描写", "後文", "test", 0.8)
    
    # エクスポートテスト
    exporter = GeoJSONExporter("test_output")
    
    print("🧪 GeoJSONエクスポートテスト")
    geojson_path = exporter.export_from_database(db, "test_bungo.geojson")
    print(f"   GeoJSON出力: {geojson_path}")
    
    stats_path = exporter.export_summary_stats(db, "test_stats.json")
    print(f"   統計情報出力: {stats_path}")
    
    csv_path = exporter.export_csv_for_analysis(db, "test_analysis.csv")
    print(f"   CSV出力: {csv_path}")
    
    db.close()


if __name__ == "__main__":
    test_geojson_exporter() 