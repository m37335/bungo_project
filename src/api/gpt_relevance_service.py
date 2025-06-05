#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT関連度判定サービス
仕様書 bungo_update_spec_draft01.md S5章 GPT関連度判定・API化に基づく実装

地名・文脈・作品の関連度をGPTで判定し、relevance≥0.8のみ可視化対象とする
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAIライブラリが利用できません。GPT関連度判定は無効化されます。")


@dataclass
class RelevanceRequest:
    """関連度判定リクエスト"""
    place_name: str
    sentence: str
    work_title: str
    author_name: str
    context: Optional[str] = None
    

@dataclass
class RelevanceResponse:
    """関連度判定レスポンス"""
    relevance_score: float
    is_relevant: bool
    reasoning: str
    execution_time: float
    

class GPTRelevanceService:
    """GPT関連度判定サービス"""
    
    def __init__(self, api_key: str = None, relevance_threshold: float = 0.8):
        """
        Args:
            api_key: OpenAI API キー
            relevance_threshold: 関連度閾値（この値以上を「関連あり」と判定）
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.relevance_threshold = relevance_threshold
        self.logger = logging.getLogger(__name__)
        
        if not OPENAI_AVAILABLE:
            self.client = None
            self.logger.warning("⚠️ OpenAIクライアント無効 - 関連度判定は常に1.0を返します")
        elif not self.api_key:
            self.client = None
            self.logger.warning("⚠️ OpenAI APIキー未設定 - 関連度判定は常に1.0を返します")
        else:
            self.client = OpenAI(api_key=self.api_key)
            self.logger.info("✅ GPT関連度判定サービス初期化完了")
    
    def judge_relevance(self, request: RelevanceRequest) -> RelevanceResponse:
        """
        単一の地名・文脈ペアの関連度を判定
        
        Args:
            request: 関連度判定リクエスト
            
        Returns:
            関連度判定結果
        """
        start_time = time.time()
        
        if not self.client:
            # フォールバック: GPT無効時は常に関連ありとして返す
            return RelevanceResponse(
                relevance_score=1.0,
                is_relevant=True,
                reasoning="GPT判定無効のため、すべて関連ありとして処理",
                execution_time=time.time() - start_time
            )
        
        try:
            prompt = self._create_relevance_prompt(request)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "あなたは文学作品と地名の関連度を判定する専門家です。"
                                  "与えられた情報から、地名が作品に実際に関連しているかを0.0-1.0の数値で判定してください。"
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1  # 一貫した判定のため低めに設定
            )
            
            response_text = response.choices[0].message.content
            score, reasoning = self._parse_gpt_response(response_text)
            
            execution_time = time.time() - start_time
            
            return RelevanceResponse(
                relevance_score=score,
                is_relevant=score >= self.relevance_threshold,
                reasoning=reasoning,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"❌ GPT関連度判定エラー: {e}")
            execution_time = time.time() - start_time
            
            # エラー時はフォールバック値を返す
            return RelevanceResponse(
                relevance_score=0.5,
                is_relevant=False,
                reasoning=f"判定エラーのため中立値: {str(e)}",
                execution_time=execution_time
            )
    
    def judge_relevance_batch(self, requests: List[RelevanceRequest]) -> List[RelevanceResponse]:
        """
        複数の地名・文脈ペアを一括で関連度判定
        
        Args:
            requests: 関連度判定リクエストのリスト
            
        Returns:
            関連度判定結果のリスト
        """
        self.logger.info(f"🔍 一括関連度判定開始: {len(requests)}件")
        
        results = []
        for i, request in enumerate(requests):
            self.logger.debug(f"判定中: {i+1}/{len(requests)} - {request.place_name}")
            
            result = self.judge_relevance(request)
            results.append(result)
            
            # API制限対策
            if self.client and i < len(requests) - 1:
                time.sleep(0.1)
        
        relevant_count = sum(1 for r in results if r.is_relevant)
        self.logger.info(f"✅ 一括関連度判定完了: {relevant_count}/{len(results)}件が関連あり")
        
        return results
    
    def filter_relevant_places(self, places_data: List[Dict]) -> List[Dict]:
        """
        地名データを関連度で絞り込み
        
        Args:
            places_data: 地名データのリスト
            
        Returns:
            関連度≥閾値の地名データのみ
        """
        if not places_data:
            return []
        
        self.logger.info(f"🎯 関連度フィルタリング開始: {len(places_data)}件")
        
        requests = []
        for place in places_data:
            request = RelevanceRequest(
                place_name=place.get('place_name', ''),
                sentence=place.get('sentence', ''),
                work_title=place.get('work_title', ''),
                author_name=place.get('author_name', ''),
                context=place.get('before_text', '') + place.get('after_text', '')
            )
            requests.append(request)
        
        responses = self.judge_relevance_batch(requests)
        
        # 関連度スコアを追加して絞り込み
        relevant_places = []
        for place, response in zip(places_data, responses):
            place_with_score = place.copy()
            place_with_score['relevance_score'] = response.relevance_score
            place_with_score['relevance_reasoning'] = response.reasoning
            
            if response.is_relevant:
                relevant_places.append(place_with_score)
        
        self.logger.info(f"✅ 関連度フィルタリング完了: {len(relevant_places)}/{len(places_data)}件が関連あり")
        
        return relevant_places
    
    def _create_relevance_prompt(self, request: RelevanceRequest) -> str:
        """関連度判定用プロンプト生成"""
        prompt = f"""
以下の情報を分析し、地名が文学作品に実際に関連しているかを判定してください。

【判定対象】
作者: {request.author_name}
作品: {request.work_title}
地名: {request.place_name}
該当文: {request.sentence}
"""
        
        if request.context:
            prompt += f"文脈: {request.context}\n"
        
        prompt += """
【判定基準】
1.0: 作品の舞台・設定として明確に使用されている
0.9: 作品に重要な役割で登場している
0.8: 作品に具体的に言及されている
0.7: 作品に関連性があるが間接的
0.6: 作品との関連性が曖昧
0.5: 関連性が不明確
0.4: 関連性が低い
0.3: ほぼ関連性がない
0.2: 関連性がない
0.1-0.0: 全く関連性がない

【出力形式】
スコア: 0.0-1.0の数値
理由: 判定理由を簡潔に説明

例:
スコア: 0.9
理由: 主人公が実際に訪れた舞台として作品中で詳細に描写されているため
"""
        
        return prompt
    
    def _parse_gpt_response(self, response_text: str) -> Tuple[float, str]:
        """GPTレスポンスをパース"""
        try:
            lines = response_text.strip().split('\n')
            score = 0.5
            reasoning = "解析失敗"
            
            for line in lines:
                line = line.strip()
                if line.startswith('スコア:') or line.startswith('Score:'):
                    # スコア抽出
                    score_text = line.split(':', 1)[1].strip()
                    score = float(score_text)
                    score = max(0.0, min(1.0, score))  # 0.0-1.0の範囲にクランプ
                elif line.startswith('理由:') or line.startswith('Reason:'):
                    # 理由抽出
                    reasoning = line.split(':', 1)[1].strip()
            
            return score, reasoning
            
        except Exception as e:
            self.logger.warning(f"⚠️ GPTレスポンス解析失敗: {e}")
            return 0.5, f"レスポンス解析エラー: {str(e)}"
    
    def get_stats(self, places_data: List[Dict]) -> Dict:
        """関連度統計取得"""
        if not places_data:
            return {
                'total_places': 0,
                'relevant_places': 0,
                'relevance_rate': 0.0,
                'avg_relevance_score': 0.0
            }
        
        total_places = len(places_data)
        relevant_places = sum(1 for p in places_data 
                            if p.get('relevance_score', 0) >= self.relevance_threshold)
        
        scores = [p.get('relevance_score', 0) for p in places_data if 'relevance_score' in p]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'total_places': total_places,
            'relevant_places': relevant_places,
            'relevance_rate': (relevant_places / total_places * 100) if total_places > 0 else 0.0,
            'avg_relevance_score': avg_score,
            'threshold': self.relevance_threshold
        }


def test_relevance_service():
    """関連度判定サービスのテスト"""
    print("🧪 GPT関連度判定サービステスト")
    
    # テストデータ
    test_requests = [
        RelevanceRequest(
            place_name="松山市",
            sentence="四国は松山の中学校に数学の教師として赴任することになった。",
            work_title="坊っちゃん",
            author_name="夏目漱石"
        ),
        RelevanceRequest(
            place_name="東京",
            sentence="東京",
            work_title="草枕",
            author_name="夏目漱石"
        ),
        RelevanceRequest(
            place_name="だんだら",
            sentence="だんだら",
            work_title="草枕", 
            author_name="夏目漱石"
        )
    ]
    
    service = GPTRelevanceService()
    
    print(f"\n🔍 単発テスト:")
    for i, req in enumerate(test_requests, 1):
        response = service.judge_relevance(req)
        print(f"{i}. 地名「{req.place_name}」")
        print(f"   スコア: {response.relevance_score:.2f}")
        print(f"   関連: {'✅' if response.is_relevant else '❌'}")
        print(f"   理由: {response.reasoning}")
        print(f"   時間: {response.execution_time:.3f}秒")
        print()
    
    print(f"🔍 一括テスト:")
    responses = service.judge_relevance_batch(test_requests)
    relevant_count = sum(1 for r in responses if r.is_relevant)
    print(f"関連あり: {relevant_count}/{len(responses)}件")
    
    # 統計テスト
    test_places = [
        {
            'place_name': req.place_name,
            'relevance_score': resp.relevance_score
        }
        for req, resp in zip(test_requests, responses)
    ]
    
    stats = service.get_stats(test_places)
    print(f"\n📊 統計:")
    print(f"総地名数: {stats['total_places']}")
    print(f"関連地名数: {stats['relevant_places']}")
    print(f"関連度率: {stats['relevance_rate']:.1f}%")
    print(f"平均スコア: {stats['avg_relevance_score']:.2f}")


if __name__ == "__main__":
    test_relevance_service() 