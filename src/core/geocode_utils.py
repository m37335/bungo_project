#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ジオコーディングユーティリティ
仕様書 bungo_update_spec_draft01.md 5章モジュール構成に基づく実装
"""

import time
import logging
import os
from typing import Dict, List, Optional, Tuple
import json

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

try:
    import googlemaps
    GOOGLEMAPS_AVAILABLE = True
except ImportError:
    GOOGLEMAPS_AVAILABLE = False


class GeocodeUtils:
    """ジオコーディングユーティリティ"""
    
    def __init__(self, google_api_key: str = None, cache_file: str = "geocode_cache.json"):
        """
        Args:
            google_api_key: Google Maps APIキー（環境変数 GOOGLE_MAPS_API_KEY からも取得）
            cache_file: ジオコーディング結果キャッシュファイル
        """
        self.logger = logging.getLogger(__name__)
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
        # Google Maps APIクライアント初期化
        self.google_api_key = google_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        if self.google_api_key and GOOGLEMAPS_AVAILABLE:
            self.gmaps = googlemaps.Client(key=self.google_api_key)
            self.logger.info("✅ Google Maps API クライアント初期化完了")
        else:
            self.gmaps = None
            self.logger.warning("⚠️ Google Maps API 未設定")
        
        # Nominatimクライアント初期化
        if GEOPY_AVAILABLE:
            self.geolocator = Nominatim(user_agent="bungo_geocoder")
            self.logger.info("✅ Nominatim ジオコーダー初期化完了")
        else:
            self.geolocator = None
            self.logger.error("❌ geopy がインストールされていません")
    
    def _load_cache(self) -> Dict:
        """キャッシュファイル読み込み"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"キャッシュ読み込み失敗: {e}")
        return {}
    
    def _save_cache(self):
        """キャッシュファイル保存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"キャッシュ保存失敗: {e}")
    
    def geocode_single(self, place_name: str, country: str = "日本") -> Dict:
        """
        単一地名のジオコーディング
        
        Args:
            place_name: 地名
            country: 国名（デフォルト：日本）
            
        Returns:
            {
                'place_name': str,
                'latitude': float,
                'longitude': float,
                'address': str,
                'geocoded': bool,
                'method': str,  # 'google', 'nominatim', 'cached', 'failed'
                'confidence': float
            }
        """
        cache_key = f"{place_name}_{country}"
        
        # キャッシュチェック
        if cache_key in self.cache:
            self.logger.debug(f"キャッシュヒット: {place_name}")
            result = self.cache[cache_key].copy()
            result['method'] = 'cached'
            return result
        
        # Google Maps API優先
        if self.gmaps:
            result = self._geocode_google(place_name, country)
            if result['geocoded']:
                self.cache[cache_key] = result
                self._save_cache()
                return result
        
        # Nominatim フォールバック
        if self.geolocator:
            result = self._geocode_nominatim(place_name, country)
            if result['geocoded']:
                self.cache[cache_key] = result
                self._save_cache()
                return result
        
        # 失敗時のレスポンス
        result = {
            'place_name': place_name,
            'latitude': None,
            'longitude': None,
            'address': None,
            'geocoded': False,
            'method': 'failed',
            'confidence': 0.0
        }
        self.cache[cache_key] = result
        self._save_cache()
        return result
    
    def _geocode_google(self, place_name: str, country: str) -> Dict:
        """Google Maps APIによるジオコーディング"""
        try:
            query = f"{place_name}, {country}"
            result = self.gmaps.geocode(query, language='ja')
            
            if result:
                location = result[0]
                return {
                    'place_name': place_name,
                    'latitude': location['geometry']['location']['lat'],
                    'longitude': location['geometry']['location']['lng'],
                    'address': location['formatted_address'],
                    'geocoded': True,
                    'method': 'google',
                    'confidence': 0.9  # Google Maps APIは高精度と仮定
                }
            
        except Exception as e:
            self.logger.warning(f"Google Maps APIエラー ({place_name}): {e}")
        
        return {'geocoded': False}
    
    def _geocode_nominatim(self, place_name: str, country: str) -> Dict:
        """Nominatimによるジオコーディング"""
        try:
            query = f"{place_name}, {country}"
            location = self.geolocator.geocode(query, timeout=10)
            
            if location:
                return {
                    'place_name': place_name,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'address': location.address,
                    'geocoded': True,
                    'method': 'nominatim',
                    'confidence': 0.7  # Nominatimは中程度の精度と仮定
                }
            
        except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable) as e:
            self.logger.warning(f"Nominatimエラー ({place_name}): {e}")
        except Exception as e:
            self.logger.error(f"Nominatim予期しないエラー ({place_name}): {e}")
        
        return {'geocoded': False}
    
    def batch_geocode(self, place_names: List[str], delay: float = 1.0) -> List[Dict]:
        """
        複数地名の一括ジオコーディング
        
        Args:
            place_names: 地名リスト
            delay: APIコール間の待機時間（秒）
            
        Returns:
            ジオコーディング結果のリスト
        """
        results = []
        total = len(place_names)
        
        self.logger.info(f"🗺️ 一括ジオコーディング開始: {total}件")
        
        for i, place_name in enumerate(place_names, 1):
            self.logger.info(f"  処理中 ({i}/{total}): {place_name}")
            
            result = self.geocode_single(place_name)
            results.append(result)
            
            if result['geocoded']:
                self.logger.info(f"    ✅ 成功 ({result['method']}): {result['latitude']:.4f}, {result['longitude']:.4f}")
            else:
                self.logger.warning(f"    ❌ 失敗: {place_name}")
            
            # API制限対策
            if i < total and result['method'] != 'cached':
                time.sleep(delay)
        
        success_count = sum(1 for r in results if r['geocoded'])
        success_rate = success_count / total * 100
        
        self.logger.info(f"✅ 一括ジオコーディング完了")
        self.logger.info(f"   成功率: {success_rate:.1f}% ({success_count}/{total})")
        
        return results
    
    def update_database_places(self, db, batch_size: int = 50) -> Dict:
        """
        データベース内のplacesテーブルをジオコーディング
        
        Args:
            db: BungoDatabaseインスタンス
            batch_size: 一度に処理する件数
            
        Returns:
            処理統計
        """
        # 未ジオコーディングの地名取得
        if hasattr(db, 'conn'):  # SQLite
            cursor = db.conn.execute(
                "SELECT place_id, place_name FROM places WHERE latitude IS NULL OR longitude IS NULL"
            )
            ungeocoded_places = cursor.fetchall()
        else:
            raise NotImplementedError("Google Sheetsのジオコーディング更新は未実装")
        
        if not ungeocoded_places:
            self.logger.info("✅ すべての地名がジオコーディング済みです")
            return {'total': 0, 'updated': 0, 'success_rate': 100.0}
        
        self.logger.info(f"🗺️ 未ジオコーディング地名: {len(ungeocoded_places)}件")
        
        updated_count = 0
        
        # バッチ処理
        for i in range(0, len(ungeocoded_places), batch_size):
            batch = ungeocoded_places[i:i + batch_size]
            place_names = [place[1] for place in batch]
            
            self.logger.info(f"バッチ {i//batch_size + 1}: {len(batch)}件処理中...")
            
            results = self.batch_geocode(place_names)
            
            # データベース更新
            for (place_id, _), result in zip(batch, results):
                if result['geocoded']:
                    # 直接UPDATE文でジオコーディング結果を更新
                    if hasattr(db, 'conn'):  # SQLite
                        db.conn.execute(
                            """UPDATE places SET 
                               latitude = ?, longitude = ?, address = ?, 
                               geocoded = ?, updated_at = CURRENT_TIMESTAMP
                               WHERE place_id = ?""",
                            (result['latitude'], result['longitude'], result['address'], 
                             True, place_id)
                        )
                        db.conn.commit()
                        updated_count += 1
        
        success_rate = updated_count / len(ungeocoded_places) * 100
        
        self.logger.info(f"✅ データベースジオコーディング完了")
        self.logger.info(f"   更新件数: {updated_count}/{len(ungeocoded_places)} ({success_rate:.1f}%)")
        
        return {
            'total': len(ungeocoded_places),
            'updated': updated_count,
            'success_rate': success_rate
        }


def test_geocode_utils():
    """ジオコーディングユーティリティのテスト"""
    geocoder = GeocodeUtils()
    
    # 単一地名テスト
    test_places = ["東京都", "松山市", "鎌倉市", "存在しない地名123"]
    
    print("🧪 単一ジオコーディングテスト")
    for place in test_places:
        result = geocoder.geocode_single(place)
        print(f"  {place}: {result['geocoded']} ({result['method']})")
        if result['geocoded']:
            print(f"    📍 {result['latitude']:.4f}, {result['longitude']:.4f}")
    
    # 一括ジオコーディングテスト
    print("\n🧪 一括ジオコーディングテスト")
    results = geocoder.batch_geocode(test_places[:3], delay=0.5)
    print(f"結果: {len([r for r in results if r['geocoded']])}/{len(results)}件成功")


if __name__ == "__main__":
    test_geocode_utils() 