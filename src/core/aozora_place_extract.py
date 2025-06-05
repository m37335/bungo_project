#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青空文庫地名抽出（正規表現ベース + GiNZA NER オプション）
仕様書 bungo_update_spec_draft01.md 5章モジュール構成に基づく実装
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

try:
    import spacy
    from spacy.lang.ja import Japanese
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import ginza
    GINZA_AVAILABLE = True
except ImportError:
    GINZA_AVAILABLE = False


class AozoraPlaceExtractor:
    """青空文庫から地名抽出（GiNZA NER使用）"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # GiNZAモデル初期化（オプション）
        self.nlp = None
        if SPACY_AVAILABLE and GINZA_AVAILABLE:
            try:
                # 最新のGiNZAは直接ja_ginzaモデルを使用
                import spacy
                self.nlp = spacy.load("ja_ginza")
                self.logger.info("✅ GiNZAモデル初期化完了")
            except OSError:
                try:
                    # ja_ginzaモデルが見つからない場合はginzaから初期化
                    import ginza
                    import spacy
                    self.nlp = spacy.blank("ja")
                    ginza.set_lang_cls(self.nlp, "ja")
                    self.logger.info("✅ GiNZA直接初期化完了")
                except Exception as e:
                    self.logger.warning(f"⚠️ GiNZA初期化失敗: {e}。正規表現ベースで動作します")
                    self.nlp = None
        else:
            self.logger.info("📝 正規表現ベースの地名抽出を使用します")
        
        # 地名ラベル（GiNZA使用時）
        # GiNZAが実際に使用するラベル：Province（都道府県）、City（市区町村）、Location（場所）
        self.location_labels = ["Province", "City", "Location", "GPE", "LOC", "FAC"]  # GiNZA地名関連ラベル
        
        # 無効地名リスト
        self.invalid_places = {
            "日", "月", "火", "水", "木", "金", "土", "年", "時", "分", "秒",
            "春", "夏", "秋", "冬", "朝", "昼", "夜", "晩",
            "今", "昨", "明", "前", "後", "間", "中", "内", "外", "上", "下",
            "左", "右", "東", "西", "南", "北", "新", "旧", "大", "小", "高", "低"
        }
        
        # 除外パターン（実在しない地名・一般名詞）
        self.exclude_patterns = {
            # 方向・抽象概念
            '東', '西', '南', '北', '上', '下', '左', '右', '前', '後', '中', '内', '外',
            # 一般的な場所名
            '家', '庭', '部屋', '階段', '廊下', '台所', '寝室', '書斎', '玄関', '窓',
            # 抽象的な場所
            '心', '頭', '手', '足', '目', '耳', '口', '顔', '体', '身体',
            # 時間関連
            '朝', '昼', '夜', '夕方', '明日', '今日', '昨日', '今年', '去年', '来年'
        }
    
    def extract_places_with_context(self, text: str, context_window: int = 1) -> List[Dict]:
        """
        テキストから地名を前後文付きで抽出
        仕様書 Seq 5: GiNZA NER で LOC/GPE 抽出、前後 1 文付与
        
        Args:
            text: 入力テキスト
            context_window: 前後文の文数
            
        Returns:
            地名抽出結果のリスト
        """
        if not self.nlp:
            self.logger.error("❌ GiNZAモデルが利用できません")
            return []
        
        # テキストを文に分割
        sentences = self._split_into_sentences(text)
        
        places = []
        
        for i, sentence in enumerate(sentences):
            # NER実行
            doc = self.nlp(sentence)
            
            for ent in doc.ents:
                if ent.label_ in self.location_labels:
                    place_name = ent.text.strip()
                    
                    # 除外パターンチェック
                    if self._should_exclude_place(place_name):
                        continue
                    
                    # 前後文抽出
                    before_text = self._get_context_sentences(sentences, i, -context_window, 0)
                    after_text = self._get_context_sentences(sentences, i, 1, context_window + 1)
                    
                    place_info = {
                        'place_name': place_name,
                        'sentence': sentence.strip(),
                        'before_text': before_text,
                        'after_text': after_text,
                        'entity_label': ent.label_,
                        'confidence': self._calculate_confidence(ent, sentence),
                        'sentence_index': i,
                        'char_start': ent.start_char,
                        'char_end': ent.end_char
                    }
                    
                    places.append(place_info)
        
        # 重複除去（同じ地名・同じ文）
        unique_places = self._remove_duplicates(places)
        
        self.logger.info(f"🗺️ 地名抽出完了: {len(unique_places)}箇所")
        return unique_places
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """テキストを文に分割"""
        # 句読点で分割
        sentences = re.split(r'[。！？\n]', text)
        
        # 空文字・短すぎる文を除外
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        return sentences
    
    def _get_context_sentences(self, sentences: List[str], current_idx: int, 
                             start_offset: int, end_offset: int) -> str:
        """前後文を取得"""
        start_idx = max(0, current_idx + start_offset)
        end_idx = min(len(sentences), current_idx + end_offset)
        
        context_sentences = sentences[start_idx:end_idx]
        return ''.join(context_sentences).strip()
    
    def _should_exclude_place(self, place_name: str) -> bool:
        """地名を除外すべきかを判定"""
        # 除外パターンに一致
        if place_name in self.exclude_patterns:
            return True
        
        # 1文字の地名は除外（方角など）
        if len(place_name) <= 1:
            return True
        
        # 数字のみは除外
        if place_name.isdigit():
            return True
        
        # ひらがなのみの短い地名は除外
        if len(place_name) <= 2 and re.match(r'^[あ-ん]+$', place_name):
            return True
        
        return False
    
    def _calculate_confidence(self, entity, sentence: str) -> float:
        """地名の信頼度を計算"""
        confidence = 0.5  # ベース信頼度
        
        # エンティティラベルによる重み付け
        if entity.label_ == 'GPE':  # 地政学的実体
            confidence += 0.3
        elif entity.label_ == 'LOC':  # 場所
            confidence += 0.2
        elif entity.label_ == 'FAC':  # 施設
            confidence += 0.1
        
        # 地名の長さによる重み付け
        if len(entity.text) >= 3:
            confidence += 0.1
        
        # 文脈による重み付け
        location_keywords = ['市', '県', '都', '府', '町', '村', '駅', '川', '山', '海', '湖', '公園', '寺', '神社']
        for keyword in location_keywords:
            if keyword in sentence:
                confidence += 0.1
                break
        
        return min(confidence, 1.0)  # 最大値は1.0
    
    def _remove_duplicates(self, places: List[Dict]) -> List[Dict]:
        """重複地名を除去"""
        seen = set()
        unique_places = []
        
        for place in places:
            # 地名と文のペアで重複チェック
            key = (place['place_name'], place['sentence'])
            
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places
    
    def extract_from_work(self, work_text: str, work_info: Dict) -> List[Dict]:
        """
        作品テキストから地名抽出（作品情報付き）
        
        Args:
            work_text: 作品テキスト
            work_info: 作品情報（author_name, title等）
            
        Returns:
            地名抽出結果のリスト（作品情報付き）
        """
        if not work_text:
            return []
        
        self.logger.info(f"📖 地名抽出開始: {work_info.get('author_name', '')} - {work_info.get('title', '')}")
        
        # テキストが長い場合はチャンク分割
        chunks = self._chunk_text(work_text, max_chars=2000)
        
        all_places = []
        
        for chunk_idx, chunk in enumerate(chunks):
            chunk_places = self.extract_places_with_context(chunk)
            
            # 作品情報を付与
            for place in chunk_places:
                place.update({
                    'author_name': work_info.get('author_name', ''),
                    'work_title': work_info.get('title', ''),
                    'aozora_id': work_info.get('aozora_id', ''),
                    'aozora_url': work_info.get('file_url', ''),
                    'chunk_index': chunk_idx,
                    'extraction_method': 'ginza'
                })
            
            all_places.extend(chunk_places)
        
        self.logger.info(f"✅ 地名抽出完了: {len(all_places)}箇所")
        return all_places
    
    def _chunk_text(self, text: str, max_chars: int = 2000) -> List[str]:
        """
        長いテキストを処理可能なサイズにチャンク分割
        句読点を考慮して自然な分割点を探す
        """
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # 文に分割
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            # チャンクに追加しても制限内か確認
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence + "。"
            else:
                # 現在のチャンクを保存
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 新しいチャンク開始
                current_chunk = sentence + "。"
        
        # 最後のチャンク
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def batch_extract_from_works(self, work_results: List[Dict]) -> List[Dict]:
        """
        複数作品から一括地名抽出
        
        Args:
            work_results: aozora_utils.batch_download_works() の結果
            
        Returns:
            全作品の地名抽出結果
        """
        all_places = []
        
        for work_result in work_results:
            if not work_result.get('success') or not work_result.get('text'):
                continue
            
            self.logger.info(f"📖 地名抽出開始: {work_result.get('author_name')} - {work_result.get('title')}")
            
            # work_resultから作品情報を抽出
            work_info = {
                'author_name': work_result.get('author_name', ''),
                'title': work_result.get('title', ''),
                'aozora_id': work_result.get('aozora_id', ''),
            }
            
            work_places = self.extract_places_from_text(work_result['text'], work_info)
            all_places.extend(work_places)
            
            self.logger.info(f"✅ 地名抽出完了: {len(work_places)}箇所")
        
        self.logger.info(f"🎯 一括地名抽出完了: {len(all_places)}箇所")
        return all_places

    def extract_places_from_text(self, text: str, work_info: Dict) -> List[Dict]:
        """
        テキストから地名を抽出
        
        Args:
            text: 対象テキスト
            work_info: 作品情報
            
        Returns:
            地名リスト
        """
        places = []
        
        if self.nlp is not None:
            # GiNZA NERを使用した地名抽出
            places.extend(self._extract_places_with_ginza(text, work_info))
        else:
            # 正規表現ベースの地名抽出（フォールバック）
            places.extend(self._extract_places_with_regex(text, work_info))
        
        return places
    
    def _extract_places_with_ginza(self, text: str, work_info: Dict) -> List[Dict]:
        """
        GiNZA NERを使用した地名抽出
        """
        places = []
        
        try:
            # テキストを適当な長さに分割（メモリ効率）
            chunk_size = 5000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                doc = self.nlp(chunk)
                
                for ent in doc.ents:
                    if ent.label_ in self.location_labels:
                        place_name = ent.text.strip()
                        if self._is_valid_place_name(place_name):
                            place_info = {
                                'place_name': place_name,
                                'author_name': work_info.get('author_name', ''),
                                'work_title': work_info.get('title', ''),
                                'extraction_method': f'ginza_ner_{ent.label_}',
                                'confidence': 0.8,  # GiNZA NERの信頼度
                                'context': self._get_context(text, ent.start_char + i, ent.end_char + i)
                            }
                            places.append(place_info)
                           
        except Exception as e:
            self.logger.error(f"❌ GiNZA地名抽出エラー: {e}")
        
        return places
    
    def _extract_places_with_regex(self, text: str, work_info: Dict) -> List[Dict]:
        """
        正規表現ベースの地名抽出（フォールバック）
        """
        places = []
        
        try:
            # 日本の地名パターン
            # 都道府県
            prefecture_patterns = [
                r'[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県]',\
                r'[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄]'\
            ]
            
            # 市区町村
            city_patterns = [
                r'[\\u4e00-\\u9faf]+[市区町村]',  # 漢字+市区町村
                r'[\\u4e00-\\u9faf]{2,}[郡]',     # 漢字+郡
            ]
            
            # 有名な地名・駅名など
            famous_places = [
                r'銀座', r'新宿', r'渋谷', r'上野', r'浅草', r'品川', r'池袋',\
                r'横浜', r'川崎', r'千葉', r'埼玉', r'大宮',\
                r'京都', r'大阪', r'神戸', r'奈良', r'名古屋',\
                r'仙台', r'札幌', r'福岡', r'広島', r'金沢',\
                r'鎌倉', r'日光', r'箱根', r'熱海', r'軽井沢'\
            ]
            
            all_patterns = prefecture_patterns + city_patterns + [pattern for pattern in famous_places]
            
            for pattern in all_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    place_name = match.group()
                    if self._is_valid_place_name(place_name):
                        place_info = {
                            'place_name': place_name,
                            'author_name': work_info.get('author_name', ''),
                            'work_title': work_info.get('title', ''),
                            'extraction_method': 'regex_pattern',
                            'confidence': 0.6,  # 正規表現の信頼度
                            'context': self._get_context(text, match.start(), match.end())
                        }
                        places.append(place_info)
       
        except Exception as e:
            self.logger.error(f"❌ 正規表現地名抽出エラー: {e}")
        
        return places

    def _is_valid_place_name(self, place_name: str) -> bool:
        """
        地名の妥当性をチェック
        """
        if not place_name or len(place_name) < 2:
            return False
        
        # 無効な地名をフィルタ
        if place_name in self.invalid_places:
            return False
        
        # 数字のみは除外
        if place_name.isdigit():
            return False
        
        return True
    
    def _get_context(self, text: str, start: int, end: int, context_len: int = 50) -> str:
        """
        地名周辺のコンテキストを取得
        """
        context_start = max(0, start - context_len)
        context_end = min(len(text), end + context_len)
        
        context = text[context_start:context_end]
        # 地名部分をハイライト
        place_part = text[start:end]
        context = context.replace(place_part, f"【{place_part}】")
        
        return context.strip()


def test_place_extractor():
    """地名抽出機能のテスト"""
    print("🧪 地名抽出テスト開始")
    
    extractor = AozoraPlaceExtractor()
    
    # テストテキスト
    test_text = """
    夏目漱石は東京で生まれ、熊本の第五高等学校で教鞭をとった。
    その後、ロンドンに留学し、帰国後は東京帝国大学で講義をおこなった。
    銀座や新宿といった都市部を舞台にした作品も多く書いている。
    鎌倉や箱根での静養中に執筆された作品もある。
    """
    
    test_work_info = {
        'author_name': '夏目漱石',
        'title': 'テスト作品',
    }
    
    # 地名抽出テスト
    places = extractor.extract_places_from_text(test_text, test_work_info)
    
    print(f"✅ 抽出された地名: {len(places)}件")
    for place in places[:5]:  # 最初の5件を表示
        print(f"  - {place['place_name']} ({place['extraction_method']}, 信頼度: {place['confidence']})")
    
    return places


if __name__ == "__main__":
    test_place_extractor() 