import wikipedia
import pandas as pd
import os
import re
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

# OpenAI APIとGoogle Sheets APIのインポートを条件付きにする
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("警告: OpenAIライブラリが利用できません。AI補完機能は無効になります。")

# Google Sheets関連のインポート（条件付き）
GSPREAD_AVAILABLE = False
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSPREAD_AVAILABLE = True
    print("📊 Google Sheets機能が利用可能です")
except ImportError:
    print("⚠️  Google Sheets機能が無効です。gspreadとoauth2clientをインストールしてください。")

class BungoCollector:
    """日本の文豪情報収集・整理システム"""
    
    def __init__(self):
        """初期設定"""
        load_dotenv()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.max_authors = int(os.getenv('MAX_AUTHORS', '50'))
        
        # Wikipedia言語設定
        wikipedia.set_lang("ja")
        
        # OpenAI設定は enhance_with_ai メソッド内で行う
        
        self.authors_data = []
        
    def get_authors_list(self) -> List[str]:
        """
        Wikipediaから日本の文豪一覧を取得
        
        Returns:
            List[str]: 文豪名のリスト
        """
        print("文豪一覧を取得中...")
        authors = []
        
        # 手動で有名な文豪を追加（主要リスト）
        famous_authors = [
            "夏目漱石", "芥川龍之介", "太宰治", "川端康成", "三島由紀夫",
            "樋口一葉", "森鴎外", "宮沢賢治", "谷崎潤一郎", "井伏鱒二",
            "坂口安吾", "石川啄木", "与謝野晶子", "正岡子規", "中原中也",
            "志賀直哉", "武者小路実篤", "有島武郎", "島崎藤村", "国木田独歩",
            "尾崎紅葉", "二葉亭四迷", "坪内逍遥", "徳田秋声", "田山花袋",
            "新美南吉", "小川未明", "立原道造", "梶井基次郎", "横光利一"
        ]
        
        authors.extend(famous_authors)
        print(f"手動リストから{len(famous_authors)}名の文豪を追加")
        
        try:
            # カテゴリから作家を取得（ボーナス）
            category_pages = [
                "日本の小説家",
                "日本の作家"
            ]
            
            for category in category_pages:
                try:
                    print(f"カテゴリ「{category}」から追加取得中...")
                    cat_page = wikipedia.page(f"Category:{category}")
                    if hasattr(cat_page, 'links'):
                        cat_members = cat_page.links
                        additional_authors = [name for name in cat_members[:10] 
                                           if self._is_valid_author_name(name) and name not in authors]
                        authors.extend(additional_authors)
                        print(f"カテゴリから{len(additional_authors)}名を追加")
                    time.sleep(1)  # API負荷軽減
                except Exception as e:
                    print(f"カテゴリ「{category}」の取得に失敗: {e}")
                    continue
                    
        except Exception as e:
            print(f"カテゴリ取得でエラー: {e}")
        
        # 重複除去と制限
        authors = list(set(authors))
        authors = [name for name in authors if self._is_valid_author_name(name)]
        authors = authors[:self.max_authors]
        
        print(f"取得完了: {len(authors)}名の文豪")
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
            print(f"「{author_name}」のWikipediaページを取得中...")
            page = wikipedia.page(author_name)
            content = page.content
            
            # 本文が短すぎる場合はスキップ
            if len(content) < 100:
                print(f"「{author_name}」: 本文が短すぎます")
                return None
                
            return content
            
        except wikipedia.exceptions.DisambiguationError as e:
            # 曖昧さ回避ページの場合、最初の候補を試す
            try:
                print(f"「{author_name}」: 曖昧さ回避ページです。最初の候補を使用します。")
                page = wikipedia.page(e.options[0])
                return page.content
            except Exception:
                print(f"「{author_name}」: 曖昧さ回避の解決に失敗")
                return None
                
        except wikipedia.exceptions.PageError:
            print(f"「{author_name}」: ページが見つかりません")
            return None
            
        except Exception as e:
            print(f"「{author_name}」: 取得エラー - {e}")
            return None
    
    def extract_works_and_places(self, author_name: str, content: str) -> Dict[str, List[str]]:
        """
        正規表現を使って作品名と所縁の地を抽出（Google Maps連携対応版）
        
        Args:
            author_name (str): 作家名
            content (str): Wikipedia本文
            
        Returns:
            Dict[str, List[str]]: 作品と詳細な場所情報のリスト
        """
        result = {
            "works": [],
            "places": [],
            "detailed_places": []  # 新設：詳細住所情報
        }
        
        # 作品名抽出（『』で囲まれたもの）
        work_pattern = r'『([^』]+)』'
        works = re.findall(work_pattern, content)
        
        # フィルタリング（長すぎる、短すぎる、数字のみなどを除外）
        filtered_works = []
        for work in works:
            if 2 <= len(work) <= 30 and not work.isdigit():
                filtered_works.append(work)
        
        result["works"] = list(set(filtered_works))[:10]  # 重複除去、最大10作品
        
        # === 詳細地名抽出機能 ===
        
        # 1. 都道府県抽出
        prefectures = [
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
            # 短縮形も含む
            "北海道", "青森", "岩手", "宮城", "秋田", "山形", "福島",
            "茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川",
            "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜",
            "静岡", "愛知", "三重", "滋賀", "京都", "大阪", "兵庫",
            "奈良", "和歌山", "鳥取", "島根", "岡山", "広島", "山口",
            "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎",
            "熊本", "大分", "宮崎", "鹿児島", "沖縄"
        ]
        
        # 2. 市区町村抽出パターン
        city_patterns = [
            r'([^\s]+市)',      # ○○市
            r'([^\s]+区)',      # ○○区  
            r'([^\s]+町)',      # ○○町
            r'([^\s]+村)',      # ○○村
            r'([^\s]+郡)',      # ○○郡
        ]
        
        # 3. 文学関連施設・記念館の抽出
        facility_patterns = [
            r'([^\s]+記念館)',
            r'([^\s]+文学館)',
            r'([^\s]+博物館)',
            r'([^\s]+資料館)',
            r'([^\s]+生家)',
            r'([^\s]+旧居)',
            r'([^\s]+墓所)',
            r'([^\s]+記念碑)',
        ]
        
        # 4. 詳細住所パターン
        address_patterns = [
            r'([^。、\s]+[都道府県][^。、\s]*[市区町村][^。、\s]*[0-9]+[-−‐][0-9]+)',  # 完全な住所
            r'([^。、\s]+[都道府県][^。、\s]*[市区町村][^。、\s]*)',  # 市区町村まで
            r'([^。、\s]+[市区町村][^。、\s]*[0-9]+[-−‐][0-9]+)',  # 番地付き
        ]
        
        # 5. 地名の種類分類キーワード
        place_type_patterns = {
            '出生地': r'(生まれ|出身|生家|故郷)',
            '居住地': r'(住|居|移住|転居|定住)',
            '活動地': r'(活動|執筆|創作|文学活動)',
            '記念館': r'(記念館|文学館|博物館|資料館)',
            '墓所': r'(墓|眠る|埋葬)',
            '作品舞台': r'(舞台|設定|描|モデル)',
        }
        
        found_places = []
        detailed_places = []
        
        # 都道府県の抽出
        for prefecture in prefectures:
            if prefecture in content:
                found_places.append(prefecture)
        
        # 市区町村の抽出
        for pattern in city_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) >= 2 and not match.isdigit():
                    found_places.append(match)
        
        # 文学関連施設の抽出
        for pattern in facility_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) >= 3:
                    detailed_places.append({
                        'name': match,
                        'type': '記念館・文学施設',
                        'context': self._extract_context(content, match)
                    })
        
        # 詳細住所の抽出
        for pattern in address_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) >= 5:
                    detailed_places.append({
                        'name': match,
                        'type': '住所',
                        'context': self._extract_context(content, match)
                    })
        
        # 地名の種類分類
        for location in found_places:
            for place_type, type_pattern in place_type_patterns.items():
                if re.search(type_pattern + r'.*' + re.escape(location), content) or \
                   re.search(re.escape(location) + r'.*' + type_pattern, content):
                    detailed_places.append({
                        'name': location,
                        'type': place_type,
                        'context': self._extract_context(content, location)
                    })
                    break
            else:
                # 種類が特定できない場合は一般的な地名として追加
                detailed_places.append({
                    'name': location,
                    'type': '関連地',
                    'context': self._extract_context(content, location)
                })
        
        # 重複除去と整理
        result["places"] = list(set(found_places))[:8]  # 従来の地名リスト
        
        # 詳細地名の重複除去
        seen_names = set()
        filtered_detailed = []
        for place in detailed_places:
            if place['name'] not in seen_names:
                seen_names.add(place['name'])
                filtered_detailed.append(place)
        
        result["detailed_places"] = filtered_detailed[:10]  # 最大10箇所
        
        print(f"「{author_name}」詳細抽出結果: 作品{len(result['works'])}件, " +
              f"地名{len(result['places'])}件, 詳細地名{len(result['detailed_places'])}件")
        
        return result
    
    def _extract_context(self, content: str, location: str, context_length: int = 50) -> str:
        """
        地名の前後の文脈を抽出してGoogle Maps検索に役立つ情報を提供
        
        Args:
            content (str): 全文
            location (str): 対象地名
            context_length (int): 前後の文字数
            
        Returns:
            str: 文脈情報
        """
        try:
            index = content.find(location)
            if index != -1:
                start = max(0, index - context_length)
                end = min(len(content), index + len(location) + context_length)
                context = content[start:end].replace('\n', ' ').strip()
                return context
            return ""
        except Exception:
            return ""
    
    def enhance_with_ai(self, author_name: str, extracted_data: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        OpenAI APIを使用して情報を補完・要約
        
        Args:
            author_name (str): 作家名
            extracted_data (Dict): 抽出済みデータ
            
        Returns:
            Dict[str, List[str]]: 補完されたデータ
        """
        if not OPENAI_AVAILABLE:
            print(f"「{author_name}」: OpenAIライブラリが利用できません。抽出データをそのまま使用します。")
            return extracted_data
            
        if not self.openai_api_key:
            print(f"「{author_name}」: OpenAI APIキーが設定されていません。抽出データをそのまま使用します。")
            return extracted_data
            
        try:
            print(f"「{author_name}」: AI補完中...")
            
            # プロンプト作成（詳細住所対応版）
            detailed_places_info = ""
            if 'detailed_places' in extracted_data and extracted_data['detailed_places']:
                detailed_places_info = "詳細地名情報:\n"
                for place in extracted_data['detailed_places'][:5]:  # 最大5件表示
                    detailed_places_info += f"- {place['name']} ({place['type']})\n"
            
            prompt = f"""
日本の文豪「{author_name}」について、Google Maps連携を想定した詳細な地理情報を含めて整理・補完してください。

現在抽出されている情報:
- 代表作: {', '.join(extracted_data['works']) if extracted_data['works'] else 'なし'}
- 所縁の地: {', '.join(extracted_data['places']) if extracted_data['places'] else 'なし'}
{detailed_places_info}

以下の形式で回答してください:

代表作:
- 作品名1
- 作品名2
- 作品名3

詳細所縁の地（Google Maps検索可能な形式で）:
- 具体的な住所または地名1（種類：出生地・居住地・記念館・墓所など）
- 具体的な住所または地名2（種類）
- 具体的な住所または地名3（種類）

記念館・文学施設:
- 施設名1（住所がわかれば併記）
- 施設名2（住所がわかれば併記）

注意事項:
- 代表作は最大5作品
- 詳細所縁の地は最大5箇所、可能な限り「○○県○○市○○町」レベルまで具体的に
- 記念館・文学施設は最大3箇所
- 住所は現在の行政区分で記載
- 不明な場合は推測せず「詳細不明」と記載
"""
            
            # OpenAI API 1.0.0以降の新しい形式
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは日本文学の専門家です。正確で簡潔な情報を提供してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # AI応答から情報を抽出
            enhanced_data = self._parse_ai_response(ai_response)
            
            print(f"「{author_name}」: AI補完完了")
            time.sleep(1)  # API制限対策
            
            return enhanced_data
            
        except Exception as e:
            print(f"「{author_name}」: AI補完エラー - {e}")
            return extracted_data
    
    def create_dataframe(self) -> pd.DataFrame:
        """
        収集したデータをDataFrameに変換（詳細住所対応版）
        
        Returns:
            pd.DataFrame: 整理されたデータ
        """
        print("データを整形中（詳細住所対応版）...")
        
        rows = []
        for author_data in self.authors_data:
            author_name = author_data['name']
            works = author_data['works']
            places = author_data['places']
            detailed_places = author_data.get('detailed_places', [])
            
            # 作品ごとに行を作成（作品がない場合は1行だけ）
            if not works:
                works = ['情報なし']
            
            # 詳細地名情報があるかチェック
            has_detailed_places = len(detailed_places) > 0
            
            for work in works:
                if has_detailed_places:
                    # 詳細地名情報がある場合：地名ごとに行を作成
                    for place_info in detailed_places:
                        row = {
                            '作家名': author_name,
                            '代表作': work,
                            '所縁の地': place_info['name'],
                            '地名種類': place_info['type'],
                            '文脈情報': place_info.get('context', '')[:100],  # 100文字まで
                            '従来の地名': ', '.join(places) if places else '情報なし'
                        }
                        rows.append(row)
                else:
                    # 従来形式のフォールバック
                    row = {
                        '作家名': author_name,
                        '代表作': work,
                        '所縁の地': ', '.join(places) if places else '情報なし',
                        '地名種類': '関連地',
                        '文脈情報': '',
                        '従来の地名': ', '.join(places) if places else '情報なし'
                    }
                    rows.append(row)
        
        df = pd.DataFrame(rows)
        print(f"DataFrame作成完了: {len(df)}行, 詳細地名対応")
        return df
    
    def create_detailed_dataframe(self) -> pd.DataFrame:
        """
        Google Maps連携特化版のDataFrameを作成
        
        Returns:
            pd.DataFrame: Google Maps用に最適化されたデータ
        """
        print("Google Maps連携用データフレーム作成中...")
        
        rows = []
        for author_data in self.authors_data:
            author_name = author_data['name']
            detailed_places = author_data.get('detailed_places', [])
            
            if detailed_places:
                for place_info in detailed_places:
                    row = {
                        '作家名': author_name,
                        '地名': place_info['name'],
                        '種類': place_info['type'],
                        '検索用地名': self._normalize_place_name(place_info['name']),
                        '文脈': place_info.get('context', '')[:200],
                        'Google Maps準備済み': '○' if self._is_maps_ready(place_info['name']) else '要確認'
                    }
                    rows.append(row)
        
        df = pd.DataFrame(rows)
        print(f"Google Maps用DataFrame作成完了: {len(df)}行")
        return df
    
    def _normalize_place_name(self, place_name: str) -> str:
        """
        Google Maps検索用に地名を正規化
        
        Args:
            place_name (str): 元の地名
            
        Returns:
            str: 正規化された地名
        """
        # 基本的な正規化
        normalized = place_name.strip()
        
        # 記念館・文学館の場合は「○○記念館」形式に統一
        if '記念館' in normalized or '文学館' in normalized:
            return normalized
        
        # 住所形式の場合はそのまま
        if '市' in normalized or '区' in normalized or '町' in normalized:
            return normalized
        
        # 都道府県名の場合は「県」を追加
        prefectures_short = [
            "青森", "岩手", "宮城", "秋田", "山形", "福島",
            "茨城", "栃木", "群馬", "埼玉", "千葉", "神奈川",
            "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜",
            "静岡", "愛知", "三重", "滋賀", "兵庫",
            "奈良", "和歌山", "鳥取", "島根", "岡山", "広島", "山口",
            "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎",
            "熊本", "大分", "宮崎", "鹿児島", "沖縄"
        ]
        
        if normalized in prefectures_short:
            return normalized + "県"
        
        return normalized
    
    def _is_maps_ready(self, place_name: str) -> bool:
        """
        Google Maps検索に適した形式かチェック
        
        Args:
            place_name (str): 地名
            
        Returns:
            bool: Maps検索準備済みかどうか
        """
        # 記念館・文学館は準備済み
        if any(facility in place_name for facility in ['記念館', '文学館', '博物館', '資料館']):
            return True
        
        # 市区町村レベルの住所は準備済み
        if any(admin in place_name for admin in ['市', '区', '町', '村']):
            return True
        
        # 番地が含まれている場合は準備済み
        if re.search(r'\d+[-−‐]\d+', place_name):
            return True
        
        return False
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = "authors.csv"):
        """
        DataFrameをCSVファイルに保存
        
        Args:
            df (pd.DataFrame): 保存するデータ
            filename (str): ファイル名
        """
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"CSV保存完了: {filename}")
        except Exception as e:
            print(f"CSV保存エラー: {e}")
    
    def save_to_google_sheets(self, df: pd.DataFrame, sheet_name: str = "日本文豪データ"):
        """
        DataFrameをGoogle Sheetsに保存（効率的バッチ処理版）
        
        Args:
            df (pd.DataFrame): 保存するデータ
            sheet_name (str): シート名
        """
        if not GSPREAD_AVAILABLE:
            print("Google Sheets機能が利用できません。gspreadライブラリをインストールしてください。")
            return
            
        if not os.path.exists(self.google_credentials_path):
            print(f"Google認証ファイルが見つかりません: {self.google_credentials_path}")
            return
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"Google Sheetsに保存中... (試行 {retry_count + 1}/{max_retries})")
                
                # 認証設定
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    self.google_credentials_path, scope)
                client = gspread.authorize(creds)
                
                # スプレッドシート作成
                sheet = client.create(sheet_name)
                worksheet = sheet.get_worksheet(0)
                
                # データの準備
                data_to_write = []
                
                # ヘッダー追加
                data_to_write.append(df.columns.tolist())
                
                # データ行追加
                for _, row in df.iterrows():
                    # NaN値を空文字に変換
                    row_data = [str(val) if pd.notna(val) else '' for val in row.tolist()]
                    data_to_write.append(row_data)
                
                print(f"データ準備完了: {len(data_to_write)}行（ヘッダー含む）")
                
                # バッチ書き込み（API制限対策）
                batch_size = 100  # 100行ずつ処理
                total_batches = (len(data_to_write) + batch_size - 1) // batch_size
                
                for i in range(0, len(data_to_write), batch_size):
                    batch_data = data_to_write[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    print(f"バッチ {batch_num}/{total_batches} 書き込み中... ({len(batch_data)}行)")
                    
                    if i == 0:
                        # 最初のバッチ：範囲を指定して一括更新
                        end_row = len(batch_data)
                        end_col_letter = self._number_to_column_letter(len(df.columns))
                        range_name = f'A1:{end_col_letter}{end_row}'
                        worksheet.update(range_name, batch_data)
                    else:
                        # 後続のバッチ：append_rows使用
                        try:
                            worksheet.append_rows(batch_data)
                        except Exception as append_error:
                            print(f"append_rows失敗、個別追加に切り替え: {append_error}")
                            # fallback: 1行ずつ追加
                            for row_data in batch_data:
                                worksheet.append_row(row_data)
                                time.sleep(0.1)  # 短い待機
                    
                    # バッチ間の待機（API制限対策）
                    if batch_num < total_batches:
                        print("API制限対策で待機中...")
                        time.sleep(2)
                
                # 共有設定（誰でも閲覧可能）
                print("共有設定中...")
                sheet.share('', perm_type='anyone', role='reader')
                
                print(f"✅ Google Sheets保存完了: {sheet.url}")
                return sheet.url  # 成功した場合はURLを返して終了
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if "RATE_LIMIT_EXCEEDED" in error_msg or "429" in error_msg:
                    wait_time = 60 * retry_count  # 指数バックオフ
                    print(f"⚠️ API制限エラー。{wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                elif "RESOURCE_EXHAUSTED" in error_msg:
                    wait_time = 120  # 2分待機
                    print(f"⚠️ リソース制限エラー。{wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Google Sheets保存エラー (試行 {retry_count}): {e}")
                    if retry_count < max_retries:
                        print(f"10秒後にリトライします...")
                        time.sleep(10)
        
        print(f"❌ Google Sheets保存失敗：{max_retries}回試行しましたが成功しませんでした")
        return None
    
    def _number_to_column_letter(self, num: int) -> str:
        """
        数値を列文字（A, B, C, ... AA, AB, ...）に変換
        
        Args:
            num (int): 列番号（1から開始）
            
        Returns:
            str: 列文字
        """
        result = ""
        while num > 0:
            num -= 1
            result = chr(num % 26 + ord('A')) + result
            num //= 26
        return result
    
    def save_to_google_sheets_efficient(self, df: pd.DataFrame, sheet_name: str = "日本文豪データ"):
        """
        より効率的なGoogle Sheets保存（小さなデータセット用）
        
        Args:
            df (pd.DataFrame): 保存するデータ
            sheet_name (str): シート名
        """
        if not GSPREAD_AVAILABLE:
            print("Google Sheets機能が利用できません。")
            return
            
        try:
            print(f"効率的Google Sheets保存開始: {sheet_name}")
            
            # 認証
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.google_credentials_path, scope)
            client = gspread.authorize(creds)
            
            # 既存のシートを検索
            try:
                sheet = client.open(sheet_name)
                print(f"既存のシート '{sheet_name}' を更新します")
                worksheet = sheet.get_worksheet(0)
                worksheet.clear()  # 既存データをクリア
            except gspread.SpreadsheetNotFound:
                # 新規作成
                sheet = client.create(sheet_name)
                worksheet = sheet.get_worksheet(0)
                print(f"新しいシート '{sheet_name}' を作成しました")
            
            # 全データを一度に更新
            all_data = [df.columns.tolist()] + df.values.tolist()
            
            # データサイズに応じて処理方法を選択
            if len(all_data) <= 1000:  # 1000行以下は一括処理
                end_col = self._number_to_column_letter(len(df.columns))
                range_name = f'A1:{end_col}{len(all_data)}'
                worksheet.update(range_name, all_data)
                print(f"一括更新完了: {len(all_data)}行")
            else:
                # 大きなデータは分割処理
                self.save_to_google_sheets(df, sheet_name)
                return
            
            # 共有設定
            sheet.share('', perm_type='anyone', role='reader')
            
            print(f"✅ 効率的保存完了: {sheet.url}")
            return sheet.url
            
        except Exception as e:
            print(f"❌ 効率的保存エラー: {e}")
            # フォールバック：通常の保存方法
            print("通常の保存方法にフォールバック...")
            return self.save_to_google_sheets(df, sheet_name)
    
    def process_all_authors(self):
        """
        全体の処理を実行（詳細住所対応版）
        """
        print("=== 日本文豪情報収集システム開始（詳細住所対応版）===")
        
        # 1. 作家一覧取得
        authors = self.get_authors_list()
        if not authors:
            print("作家一覧の取得に失敗しました。")
            return
        
        # 2. 各作家の情報収集
        for i, author in enumerate(authors, 1):
            print(f"\n[{i}/{len(authors)}] 処理中: {author}")
            
            # Wikipedia本文取得
            content = self.get_wikipedia_content(author)
            if not content:
                continue
            
            # 初期抽出（詳細地名情報も含む）
            extracted_data = self.extract_works_and_places(author, content)
            
            # AI補完
            enhanced_data = self.enhance_with_ai(author, extracted_data)
            
            # データ保存（詳細地名情報も保存）
            author_record = {
                'name': author,
                'works': enhanced_data['works'],
                'places': enhanced_data['places']
            }
            
            # 詳細地名情報も保存
            if 'detailed_places' in extracted_data:
                author_record['detailed_places'] = extracted_data['detailed_places']
            
            self.authors_data.append(author_record)
            
            # 進捗表示
            if i % 5 == 0:
                print(f"進捗: {i}/{len(authors)} 完了")
        
        # 3. データ整形と出力
        if self.authors_data:
            # 標準データフレーム作成（詳細住所対応）
            df = self.create_dataframe()
            
            # Google Maps特化データフレーム作成
            maps_df = self.create_detailed_dataframe()
            
            # CSV出力
            self.save_to_csv(df, "authors_detailed.csv")
            if not maps_df.empty:
                self.save_to_csv(maps_df, "authors_googlemaps.csv")
            
            # Google Sheets出力
            if GSPREAD_AVAILABLE:
                self.save_to_google_sheets(df, "日本文豪データ（詳細住所版）")
                if not maps_df.empty:
                    self.save_to_google_sheets(maps_df, "日本文豪GoogleMaps用データ")
            else:
                print("Google Sheets出力をスキップしました（gspreadライブラリが利用できません）")
            
            # 統計情報表示
            print(f"\n=== 処理完了 ===")
            print(f"処理した作家数: {len(self.authors_data)}")
            print(f"標準データ出力行数: {len(df)}")
            print(f"Google Maps用データ出力行数: {len(maps_df)}")
            
            # 詳細地名抽出統計
            total_detailed_places = sum(len(data.get('detailed_places', [])) for data in self.authors_data)
            maps_ready_count = len([row for _, row in maps_df.iterrows() if row['Google Maps準備済み'] == '○'])
            
            print(f"抽出した詳細地名数: {total_detailed_places}")
            print(f"Google Maps準備済み地名数: {maps_ready_count}")
            print(f"Google Maps準備率: {maps_ready_count/len(maps_df)*100:.1f}%" if len(maps_df) > 0 else "Google Maps準備率: N/A")
            
        else:
            print("収集できたデータがありません。")
    
    def _parse_ai_response(self, response: str) -> Dict[str, List[str]]:
        """
        AI応答から構造化データを抽出
        
        Args:
            response (str): AI応答テキスト
            
        Returns:
            Dict[str, List[str]]: 抽出されたデータ
        """
        result = {"works": [], "places": []}
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if '代表作:' in line:
                current_section = 'works'
            elif '所縁の地:' in line:
                current_section = 'places'
            elif line.startswith('- ') and current_section:
                item = line[2:].strip()
                if current_section == 'works':
                    result['works'].append(item)
                elif current_section == 'places':
                    # 括弧内の説明を除去
                    place = re.sub(r'（.+?）', '', item).strip()
                    result['places'].append(place)
        
        return result
    
    def _is_valid_author_name(self, name: str) -> bool:
        """
        有効な文豪名かチェック
        
        Args:
            name (str): チェックする名前
            
        Returns:
            bool: 有効な名前の場合True
        """
        # 除外パターン
        exclude_patterns = [
            r'^\d',  # 数字で始まる
            r'Category:',  # カテゴリページ
            r'Template:',  # テンプレートページ
            r'List of',  # リストページ
            r'一覧$',  # 一覧で終わる
            r'年$',  # 年で終わる
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, name):
                return False
        
        # 日本語文字が含まれているかチェック（Unicode範囲で判定）
        japanese_chars = False
        for char in name:
            # ひらがな、カタカナ、漢字のUnicode範囲
            if ('\u3040' <= char <= '\u309F') or \
               ('\u30A0' <= char <= '\u30FF') or \
               ('\u4E00' <= char <= '\u9FFF'):
                japanese_chars = True
                break
        
        return japanese_chars and len(name) >= 2 and len(name) <= 10
    
    def export_for_googlemaps(self, output_file: str = "googlemaps_export.csv"):
        """
        Google Maps用の特別なエクスポート機能
        
        Args:
            output_file (str): 出力ファイル名
        """
        print("Google Maps用エクスポート作成中...")
        
        maps_data = []
        for author_data in self.authors_data:
            author_name = author_data['name']
            detailed_places = author_data.get('detailed_places', [])
            
            for place_info in detailed_places:
                maps_entry = {
                    '作家名': author_name,
                    '地名': place_info['name'],
                    '種類': place_info['type'],
                    '検索クエリ': self._create_maps_query(author_name, place_info),
                    'Maps URL': self._create_maps_url(place_info['name']),
                    '文脈': place_info.get('context', '')[:150],
                    '準備状況': '○' if self._is_maps_ready(place_info['name']) else '要確認'
                }
                maps_data.append(maps_entry)
        
        if maps_data:
            df = pd.DataFrame(maps_data)
            self.save_to_csv(df, output_file)
            print(f"Google Maps用エクスポート完了: {output_file}")
            return df
        else:
            print("Google Maps用データがありません。")
            return pd.DataFrame()
    
    def _create_maps_query(self, author_name: str, place_info: Dict) -> str:
        """
        Google Maps検索用クエリを生成
        
        Args:
            author_name (str): 作家名
            place_info (Dict): 地名情報
            
        Returns:
            str: 検索クエリ
        """
        place_name = place_info['name']
        place_type = place_info['type']
        
        # 記念館・文学館の場合
        if place_type == '記念館・文学施設' or '記念館' in place_name:
            return f"{place_name}"
        
        # 墓所の場合
        elif place_type == '墓所':
            return f"{author_name} 墓所 {place_name}"
        
        # 出生地・居住地の場合
        elif place_type in ['出生地', '居住地']:
            return f"{place_name} {author_name}"
        
        # その他の場合
        else:
            return place_name
    
    def _create_maps_url(self, place_name: str) -> str:
        """
        Google Maps URLを生成
        
        Args:
            place_name (str): 地名
            
        Returns:
            str: Google Maps URL
        """
        import urllib.parse
        query = urllib.parse.quote(place_name)
        return f"https://www.google.com/maps/search/{query}"
    
    def generate_maps_summary(self) -> Dict[str, int]:
        """
        Google Maps連携用の統計情報を生成
        
        Returns:
            Dict[str, int]: 統計情報
        """
        stats = {
            '総地名数': 0,
            '記念館・文学施設': 0,
            '出生地': 0,
            '居住地': 0,
            '墓所': 0,
            'Maps準備済み': 0,
            '要確認': 0
        }
        
        for author_data in self.authors_data:
            detailed_places = author_data.get('detailed_places', [])
            stats['総地名数'] += len(detailed_places)
            
            for place_info in detailed_places:
                place_type = place_info['type']
                if place_type in stats:
                    stats[place_type] += 1
                
                if self._is_maps_ready(place_info['name']):
                    stats['Maps準備済み'] += 1
                else:
                    stats['要確認'] += 1
        
        return stats
        
if __name__ == "__main__":
    collector = BungoCollector()
    collector.process_all_authors() 