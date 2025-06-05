#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S5機能完了確認テスト（GPT関連度判定・API化）
仕様書 S5: GPT関連度判定・差分配信API / relevance≥0.8のみ可視化
"""

import time
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List

import requests
from gpt_relevance_service import GPTRelevanceService, RelevanceRequest
from db_utils import BungoDatabase

# ログ設定
logging.basicConfig(level=logging.INFO)

class S5APITester:
    """S5 API機能テスター"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.db_path = "test_ginza.db"
        
    def test_s5_completion(self) -> bool:
        """S5機能の完了確認テスト"""
        print("🎯 S5機能完了確認テスト開始")
        print("目標: GPT関連度判定・API化 / relevance≥0.8のみ可視化")
        
        # 前提条件確認
        if not Path(self.db_path).exists():
            print(f"❌ テストデータベースが見つかりません: {self.db_path}")
            return False
        
        # テスト実行
        tests = [
            ("1. GPT関連度判定サービス", self.test_gpt_relevance_service),
            ("2. API サーバー基本機能", self.test_api_basic),
            ("3. 検索API エンドポイント", self.test_search_endpoints),
            ("4. GPT関連度判定API", self.test_gpt_api),
            ("5. GeoJSONエクスポートAPI", self.test_geojson_export),
            ("6. 関連度フィルタリング", self.test_relevance_filtering),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}")
            try:
                result = test_func()
                status = "✅ 成功" if result else "❌ 失敗"
                print(f"   結果: {status}")
                results.append(result)
            except Exception as e:
                print(f"   結果: ❌ エラー - {e}")
                results.append(False)
        
        # 総合判定
        success_count = sum(results)
        total_count = len(results)
        overall_success = success_count == total_count
        
        print(f"\n🎯 S5機能完了確認結果:")
        print(f"   成功テスト: {success_count}/{total_count}")
        print(f"   S5機能完了: {'✅ 完全達成' if overall_success else '❌ 未完了'}")
        
        if overall_success:
            print(f"\n🎉 S5機能が正常に完了しました！")
            print(f"   API サーバー: {self.base_url}")
            print(f"   OpenAPI ドキュメント: {self.base_url}/docs")
            print(f"   ReDoc ドキュメント: {self.base_url}/redoc")
        
        return overall_success
    
    def test_gpt_relevance_service(self) -> bool:
        """GPT関連度判定サービスのテスト"""
        try:
            service = GPTRelevanceService()
            
            # テストリクエスト
            test_requests = [
                RelevanceRequest(
                    place_name="松山市",
                    sentence="四国は松山の中学校に数学の教師として赴任することになった。",
                    work_title="坊っちゃん",
                    author_name="夏目漱石"
                ),
                RelevanceRequest(
                    place_name="だんだら",
                    sentence="だんだら",
                    work_title="草枕",
                    author_name="夏目漱石"
                )
            ]
            
            print(f"   💭 単発関連度判定テスト:")
            for req in test_requests:
                response = service.judge_relevance(req)
                print(f"      地名「{req.place_name}」: スコア {response.relevance_score:.2f} {'✅' if response.is_relevant else '❌'}")
            
            print(f"   💭 一括関連度判定テスト:")
            responses = service.judge_relevance_batch(test_requests)
            relevant_count = sum(1 for r in responses if r.is_relevant)
            print(f"      関連あり: {relevant_count}/{len(responses)}件")
            
            return True
            
        except Exception as e:
            print(f"      ❌ GPTサービステストエラー: {e}")
            return False
    
    def test_api_basic(self) -> bool:
        """API サーバー基本機能テスト"""
        try:
            # ヘルスチェック
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"      ❌ ヘルスチェック失敗: {response.status_code}")
                return False
            
            health_data = response.json()
            print(f"      ✅ ヘルスチェック: {health_data['status']}")
            
            # 統計取得
            response = requests.get(f"{self.base_url}/stats", timeout=5)
            if response.status_code != 200:
                print(f"      ❌ 統計取得失敗: {response.status_code}")
                return False
            
            stats_data = response.json()
            print(f"      ✅ 統計: 作者{stats_data['authors_count']}名, 作品{stats_data['works_count']}件, 地名{stats_data['places_count']}箇所")
            
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"      ❌ API サーバーに接続できません: {self.base_url}")
            print(f"         💡 以下コマンドでサーバーを起動してください:")
            print(f"         python api_server.py")
            return False
        except Exception as e:
            print(f"      ❌ API基本テストエラー: {e}")
            return False
    
    def test_search_endpoints(self) -> bool:
        """検索API エンドポイントテスト"""
        try:
            # 作者検索
            response = requests.get(f"{self.base_url}/search/authors", params={"q": "夏目"}, timeout=10)
            if response.status_code != 200:
                print(f"      ❌ 作者検索失敗: {response.status_code}")
                return False
            
            author_data = response.json()
            print(f"      ✅ 作者検索: {len(author_data['authors'])}名, 実行時間{author_data['execution_time']:.3f}秒")
            
            # 作品検索
            response = requests.get(f"{self.base_url}/search/works", params={"q": "草枕"}, timeout=10)
            if response.status_code != 200:
                print(f"      ❌ 作品検索失敗: {response.status_code}")
                return False
            
            work_data = response.json()
            print(f"      ✅ 作品検索: {len(work_data['works'])}件, 地名{len(work_data['places'])}箇所")
            
            # 地名検索
            response = requests.get(f"{self.base_url}/search/places", params={"q": "東京"}, timeout=10)
            if response.status_code != 200:
                print(f"      ❌ 地名検索失敗: {response.status_code}")
                return False
            
            place_data = response.json()
            print(f"      ✅ 地名検索: {len(place_data['places'])}箇所, 関連作者{len(place_data['authors'])}名")
            
            return True
            
        except Exception as e:
            print(f"      ❌ 検索APIテストエラー: {e}")
            return False
    
    def test_gpt_api(self) -> bool:
        """GPT関連度判定APIテスト"""
        try:
            # 単発関連度判定
            test_request = {
                "place_name": "松山市",
                "sentence": "四国は松山の中学校に数学の教師として赴任することになった。",
                "work_title": "坊っちゃん",
                "author_name": "夏目漱石"
            }
            
            response = requests.post(f"{self.base_url}/gpt/relevance", json=test_request, timeout=30)
            if response.status_code != 200:
                print(f"      ❌ GPT関連度判定失敗: {response.status_code}")
                return False
            
            relevance_data = response.json()
            print(f"      ✅ GPT関連度判定: スコア{relevance_data['relevance_score']:.2f}, 実行時間{relevance_data['execution_time']:.3f}秒")
            
            # 一括関連度判定
            batch_request = {
                "items": [
                    test_request,
                    {
                        "place_name": "だんだら",
                        "sentence": "だんだら",
                        "work_title": "草枕",
                        "author_name": "夏目漱石"
                    }
                ]
            }
            
            response = requests.post(f"{self.base_url}/gpt/batch-relevance", json=batch_request, timeout=60)
            if response.status_code != 200:
                print(f"      ❌ GPT一括関連度判定失敗: {response.status_code}")
                return False
            
            batch_data = response.json()
            print(f"      ✅ GPT一括判定: {batch_data['relevant_count']}/{batch_data['total_count']}件関連あり")
            
            return True
            
        except Exception as e:
            print(f"      ❌ GPT APIテストエラー: {e}")
            return False
    
    def test_geojson_export(self) -> bool:
        """GeoJSONエクスポートAPIテスト"""
        try:
            # デフォルト閾値（0.8）でエクスポート
            response = requests.get(f"{self.base_url}/export/geojson", timeout=60)
            if response.status_code != 200:
                print(f"      ❌ GeoJSONエクスポート失敗: {response.status_code}")
                return False
            
            # Content-Type確認
            content_type = response.headers.get('content-type', '')
            if 'geo+json' not in content_type and 'json' not in content_type:
                print(f"      ❌ 不正なContent-Type: {content_type}")
                return False
            
            geojson_data = response.json()
            
            # GeoJSON形式確認
            if geojson_data.get('type') != 'FeatureCollection':
                print(f"      ❌ 不正なGeoJSON形式")
                return False
            
            features = geojson_data.get('features', [])
            print(f"      ✅ GeoJSONエクスポート: {len(features)}箇所の地名データ")
            
            # 関連度フィルタテスト
            response = requests.get(f"{self.base_url}/export/geojson", params={"relevance_threshold": 0.9}, timeout=60)
            if response.status_code == 200:
                high_relevance_data = response.json()
                high_features = high_relevance_data.get('features', [])
                print(f"      ✅ 高関連度フィルタ（≥0.9）: {len(high_features)}箇所")
            
            return True
            
        except Exception as e:
            print(f"      ❌ GeoJSONエクスポートテストエラー: {e}")
            return False
    
    def test_relevance_filtering(self) -> bool:
        """関連度フィルタリング機能テスト"""
        try:
            # データベースから地名データ取得
            db = BungoDatabase("sqlite", self.db_path)
            places = db.search_places("")
            db.close()
            
            if not places:
                print(f"      ❌ テストデータなし")
                return False
            
            # GPTサービスでフィルタリング
            gpt_service = GPTRelevanceService()
            
            # サンプルデータでテスト（時間短縮のため最大5件）
            test_places = places[:5]
            filtered_places = gpt_service.filter_relevant_places(test_places)
            
            # 統計取得
            stats = gpt_service.get_stats(filtered_places)
            
            print(f"      ✅ 関連度フィルタリング:")
            print(f"         元データ: {len(test_places)}件")
            print(f"         関連あり: {len(filtered_places)}件")
            print(f"         関連度率: {stats['relevance_rate']:.1f}%")
            print(f"         平均スコア: {stats['avg_relevance_score']:.2f}")
            print(f"         閾値: {stats['threshold']}")
            
            return True
            
        except Exception as e:
            print(f"      ❌ 関連度フィルタリングテストエラー: {e}")
            return False


def test_s5_completion():
    """S5機能完了確認のメイン関数"""
    tester = S5APITester()
    return tester.test_s5_completion()


if __name__ == "__main__":
    success = test_s5_completion()
    exit(0 if success else 1) 