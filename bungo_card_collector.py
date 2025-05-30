#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本の文豪地図カード生成システム（スリム版）
地図表示専用に最適化されたシンプルバージョン
"""

import wikipedia
import pandas as pd
import os
import re
import time
from typing import List, Dict, Optional

# OpenAI APIのインポート（条件付き）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("ℹ️ OpenAIライブラリが利用できません。基本機能のみ使用します。")

class BungoCardCollector:
    """日本の文豪地図カード生成システム（地図表示特化版）"""
    
    def __init__(self):
        """初期設定"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.max_authors = int(os.getenv('MAX_AUTHORS', '15'))  # 地図表示には適量
        
        # Wikipedia言語設定
        wikipedia.set_lang("ja")
        
        self.authors_data = []
        
    def get_authors_list(self) -> List[str]:
        """
        文豪一覧を取得（地図表示用に厳選）
        
        Returns:
            List[str]: 文豪名のリスト
        """
        print("📚 文豪一覧を取得中...")
        
        # 地図表示に適した有名文豪リスト（厳選版）
        famous_authors = [
            "夏目漱石", "芥川龍之介", "太宰治", "川端康成", "三島由紀夫",
            "宮沢賢治", "谷崎潤一郎", "森鴎外", "樋口一葉", "石川啄木",
            "与謝野晶子", "正岡子規", "中原中也", "志賀直哉", "武者小路実篤",
            "有島武郎", "島崎藤村", "国木田独歩", "尾崎紅葉", "井伏鱒二"
        ]
        
        # 指定数に制限
        authors = famous_authors[:self.max_authors]
        
        print(f"✅ 地図表示用文豪: {len(authors)}名")
        return authors
    
    def get_wikipedia_content(self, author_name: str) -> Optional[str]:
        """
        指定した作家のWikipediaページの本文を取得
        
        Args:
            author_name (str): 作家名
            
        Returns:
            Optional[str]: Wikipedia本文、取得失敗時はNone
        """
        try:
            print(f"📖 「{author_name}」のWikipedia情報取得中...")
            page = wikipedia.page(author_name)
            content = page.content
            
            if len(content) < 100:
                print(f"⚠️ 「{author_name}」: 本文が短すぎます")
                return None
                
            return content
            
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                print(f"🔀 「{author_name}」: 曖昧さ回避ページ - 最初の候補を使用")
                page = wikipedia.page(e.options[0])
                return page.content
            except Exception:
                print(f"❌ 「{author_name}」: 曖昧さ回避の解決に失敗")
                return None
                
        except wikipedia.exceptions.PageError:
            print(f"❌ 「{author_name}」: ページが見つかりません")
            return None
            
        except Exception as e:
            print(f"❌ 「{author_name}」: 取得エラー - {e}")
            return None
    
    def extract_works_and_places(self, author_name: str, content: str) -> Dict[str, List[str]]:
        """
        作品名と地名を抽出（地図カード用に最適化）
        
        Args:
            author_name (str): 作家名
            content (str): Wikipedia本文
            
        Returns:
            Dict[str, List[str]]: 作品と地名の詳細情報
        """
        result = {
            "works": [],
            "places": [],
            "detailed_places": []
        }
        
        # 作品名抽出（『』で囲まれたもの）
        work_pattern = r'『([^』]+)』'
        works = re.findall(work_pattern, content)
        
        # 作品名フィルタリング
        filtered_works = []
        for work in works:
            if 2 <= len(work) <= 30 and not work.isdigit():
                filtered_works.append(work)
        
        result["works"] = list(set(filtered_works))[:5]  # 地図表示用に5作品まで
        
        # 詳細地名抽出（地図表示に重要）
        detailed_places = []
        
        # 1. 都道府県
        prefectures = [
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
            # 短縮形
            "東京", "京都", "大阪", "神奈川", "愛知", "福岡", "北海道"
        ]
        
        # 2. 市区町村
        city_patterns = [
            r'([^\s]+市)', r'([^\s]+区)', r'([^\s]+町)', r'([^\s]+村)', r'([^\s]+郡)'
        ]
        
        # 3. 文学施設
        facility_patterns = [
            r'([^\s]*記念館[^\s]*)', r'([^\s]*文学館[^\s]*)', 
            r'([^\s]*博物館[^\s]*)', r'([^\s]*資料館[^\s]*)',
            r'([^\s]*生家[^\s]*)', r'([^\s]*旧居[^\s]*)',
            r'([^\s]*墓所[^\s]*)', r'([^\s]*記念碑[^\s]*)'
        ]
        
        # 地名抽出実行
        for prefecture in prefectures:
            if prefecture in content:
                context = self._extract_context(content, prefecture)
                place_type = self._classify_place_type(context)
                detailed_places.append({
                    'name': prefecture,
                    'type': place_type,
                    'context': context,
                    'maps_ready': self._is_maps_ready(prefecture)
                })
        
        for pattern in city_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) > 1:
                    context = self._extract_context(content, match)
                    place_type = self._classify_place_type(context)
                    detailed_places.append({
                        'name': match,
                        'type': place_type,
                        'context': context,
                        'maps_ready': self._is_maps_ready(match)
                    })
        
        for pattern in facility_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) > 2:
                    context = self._extract_context(content, match)
                    detailed_places.append({
                        'name': match,
                        'type': '記念館・文学施設',
                        'context': context,
                        'maps_ready': True  # 文学施設は地図表示に適している
                    })
        
        # 重複除去と制限
        unique_places = []
        seen = set()
        for place in detailed_places:
            if place['name'] not in seen and len(place['name']) >= 2:
                unique_places.append(place)
                seen.add(place['name'])
                if len(unique_places) >= 10:  # 地図表示用に制限
                    break
        
        result["detailed_places"] = unique_places
        result["places"] = [p['name'] for p in unique_places]
        
        return result
    
    def _extract_context(self, content: str, location: str, context_length: int = 80) -> str:
        """文脈情報を抽出"""
        try:
            index = content.find(location)
            if index == -1:
                return ""
            
            start = max(0, index - context_length)
            end = min(len(content), index + len(location) + context_length)
            context = content[start:end].replace('\n', ' ').strip()
            
            return context
        except Exception:
            return ""
    
    def _classify_place_type(self, context: str) -> str:
        """地名の種類を分類"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['生', '誕生', '出身', '故郷']):
            return '出生地'
        elif any(word in context_lower for word in ['住', '居住', '暮らし', '生活']):
            return '居住地'
        elif any(word in context_lower for word in ['活動', '執筆', '創作', '文学']):
            return '活動地'
        elif any(word in context_lower for word in ['記念館', '文学館', '博物館']):
            return '記念館・文学施設'
        elif any(word in context_lower for word in ['墓', '眠る', '葬']):
            return '墓所'
        elif any(word in context_lower for word in ['舞台', '背景', '作品']):
            return '作品舞台'
        else:
            return 'ゆかりの地'
    
    def _is_maps_ready(self, place_name: str) -> bool:
        """Google Maps検索に適しているかチェック"""
        # 記念館・文学館は準備済み
        if any(facility in place_name for facility in ['記念館', '文学館', '博物館', '資料館']):
            return True
        
        # 市区町村レベルは準備済み
        if any(admin in place_name for admin in ['市', '区', '町', '村']):
            return True
        
        # 有名な都道府県は準備済み
        famous_prefectures = ['東京', '京都', '大阪', '神奈川', '愛知', '福岡', '北海道']
        if any(pref in place_name for pref in famous_prefectures):
            return True
        
        return False
    
    def enhance_with_ai(self, author_name: str, extracted_data: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        AI補完機能（オプション）
        
        Args:
            author_name (str): 作家名
            extracted_data (Dict): 抽出されたデータ
            
        Returns:
            Dict[str, List[str]]: 補完されたデータ
        """
        if not OPENAI_AVAILABLE or not self.openai_api_key:
            print(f"ℹ️ {author_name}: AI補完をスキップ（APIキー未設定）")
            return extracted_data
        
        try:
            client = OpenAI(api_key=self.openai_api_key)
            
            prompt = f"""
            文豪「{author_name}」について、地図カード表示用の情報を整理してください。
            
            抽出された情報:
            - 代表作: {', '.join(extracted_data['works'])}
            - 所縁の地: {', '.join(extracted_data['places'])}
            
            以下の形式で回答してください:
            代表作: [作品名を3つまで、カンマ区切り]
            所縁の地: [地名を5つまで、カンマ区切り]
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            enhanced_data = self._parse_ai_response(ai_response)
            
            # AI結果とマージ
            if enhanced_data['works']:
                extracted_data['works'] = enhanced_data['works']
            if enhanced_data['places']:
                # 既存の詳細地名情報は保持
                extracted_data['places'].extend(enhanced_data['places'])
                extracted_data['places'] = list(set(extracted_data['places']))[:10]
            
            print(f"✨ {author_name}: AI補完完了")
            
        except Exception as e:
            print(f"⚠️ {author_name}: AI補完エラー - {e}")
        
        return extracted_data
    
    def _parse_ai_response(self, response: str) -> Dict[str, List[str]]:
        """AI応答を解析"""
        result = {"works": [], "places": []}
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if '代表作:' in line:
                works_str = line.split('代表作:')[1].strip()
                result['works'] = [w.strip() for w in works_str.split(',') if w.strip()]
            elif '所縁の地:' in line:
                places_str = line.split('所縁の地:')[1].strip()
                result['places'] = [p.strip() for p in places_str.split(',') if p.strip()]
        
        return result
    
    def create_map_cards(self) -> pd.DataFrame:
        """
        地図カード用データを生成
        
        Returns:
            pd.DataFrame: 地図カード用データ
        """
        print("🗺️ 地図カード用データ生成中...")
        
        card_data = []
        
        for author_data in self.authors_data:
            author_name = author_data['name']
            works = author_data.get('works', ['代表作'])
            detailed_places = author_data.get('detailed_places', [])
            
            # 各地名に対してカードを作成
            for place_info in detailed_places:
                place_name = place_info['name']
                place_type = place_info['type']
                context = place_info['context']
                maps_ready = place_info['maps_ready']
                
                # 代表作を選択（最初の作品を使用）
                representative_work = works[0] if works else "代表作品"
                
                # カード用説明文を生成
                description = f"{author_name}の{representative_work}ゆかりの{place_type}です。"
                if context and len(context) > 20:
                    description += f" {context[:120]}..."
                
                # Google Maps URL生成
                maps_url = f"https://www.google.com/maps/search/{place_name}"
                
                card = {
                    'card_id': f"card_{len(card_data) + 1}",
                    '作品名': representative_work,
                    '作者名': author_name,
                    'ゆかりの土地': place_name,
                    '内容説明': description,
                    '地名種類': place_type,
                    'Maps_URL': maps_url,
                    'Maps準備済み': '○' if maps_ready else '要確認'
                }
                
                card_data.append(card)
        
        df = pd.DataFrame(card_data)
        
        print(f"✅ 地図カード生成完了: {len(df)}枚")
        return df
    
    def save_map_cards(self, df: pd.DataFrame, filename: str = "map_cards.csv"):
        """地図カード用CSVを保存"""
        try:
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"💾 地図カード保存完了: {filename}")
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
    
    def process_all_authors(self):
        """
        全体処理を実行（地図カード生成特化版）
        """
        print("🚀 日本文豪地図カード生成システム開始")
        print("=" * 50)
        
        # 1. 作家一覧取得
        authors = self.get_authors_list()
        if not authors:
            print("❌ 作家一覧の取得に失敗しました")
            return
        
        # 2. 各作家の情報収集
        for i, author in enumerate(authors, 1):
            print(f"\n[{i}/{len(authors)}] 処理中: {author}")
            
            # Wikipedia本文取得
            content = self.get_wikipedia_content(author)
            if not content:
                continue
            
            # 作品・地名抽出
            extracted_data = self.extract_works_and_places(author, content)
            
            # AI補完（オプション）
            enhanced_data = self.enhance_with_ai(author, extracted_data)
            
            # データ保存
            self.authors_data.append({
                'name': author,
                'works': enhanced_data['works'],
                'places': enhanced_data['places'],
                'detailed_places': enhanced_data['detailed_places']
            })
            
            # 進捗表示
            if i % 3 == 0:
                print(f"📊 進捗: {i}/{len(authors)} 完了")
        
        # 3. 地図カード生成・保存
        if self.authors_data:
            # 地図カード生成
            cards_df = self.create_map_cards()
            
            # CSV保存
            self.save_map_cards(cards_df, "map_cards.csv")
            
            # 統計表示
            maps_ready_count = len(cards_df[cards_df['Maps準備済み'] == '○'])
            maps_ready_rate = maps_ready_count / len(cards_df) * 100 if len(cards_df) > 0 else 0
            
            print(f"\n🎯 処理完了！")
            print(f"📚 処理文豪数: {len(self.authors_data)}人")
            print(f"🗺️ 生成カード数: {len(cards_df)}枚")
            print(f"✅ Maps準備済み: {maps_ready_count}枚 ({maps_ready_rate:.1f}%)")
            print(f"📁 出力ファイル: map_cards.csv")
            print(f"\n🎉 地図表示システム準備完了！")
            
            return cards_df
        else:
            print("❌ 収集できたデータがありません")
            return None

def main():
    """メイン実行関数"""
    print("🗺️ 日本文豪地図カード生成システム（スリム版）")
    print("地図表示に特化した軽量システムです")
    
    collector = BungoCardCollector()
    result = collector.process_all_authors()
    
    if result is not None:
        print("\n📋 生成されたカードサンプル:")
        for i, row in result.head(3).iterrows():
            print(f"\n--- カード {i+1} ---")
            print(f"作品: {row['作品名']}")
            print(f"作者: {row['作者名']}")
            print(f"場所: {row['ゆかりの土地']}")
            print(f"説明: {row['内容説明'][:100]}...")

if __name__ == "__main__":
    main() 