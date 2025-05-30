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
        正規表現を使って作品名と所縁の地を抽出
        
        Args:
            author_name (str): 作家名
            content (str): Wikipedia本文
            
        Returns:
            Dict[str, List[str]]: 作品と場所のリスト
        """
        result = {
            "works": [],
            "places": []
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
        
        # 地名抽出（都道府県名、有名な市名など）
        place_keywords = [
            # 都道府県
            "北海道", "青森", "岩手", "宮城", "秋田", "山形", "福島",
            "茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川",
            "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜",
            "静岡", "愛知", "三重", "滋賀", "京都", "大阪", "兵庫",
            "奈良", "和歌山", "鳥取", "島根", "岡山", "広島", "山口",
            "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎",
            "熊本", "大分", "宮崎", "鹿児島", "沖縄",
            # 主要都市
            "札幌", "仙台", "横浜", "名古屋", "神戸", "福岡"
        ]
        
        found_places = []
        for place in place_keywords:
            if place in content:
                found_places.append(place)
        
        result["places"] = list(set(found_places))[:5]  # 重複除去、最大5箇所
        
        print(f"「{author_name}」抽出結果: 作品{len(result['works'])}件, 場所{len(result['places'])}件")
        return result
    
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
            
            # プロンプト作成
            prompt = f"""
日本の文豪「{author_name}」について、以下の情報を整理・補完してください。

現在抽出されている情報:
- 代表作: {', '.join(extracted_data['works']) if extracted_data['works'] else 'なし'}
- 所縁の地: {', '.join(extracted_data['places']) if extracted_data['places'] else 'なし'}

以下の形式で回答してください:
代表作:
- 作品名1
- 作品名2
- 作品名3

所縁の地:
- 地名1（理由）
- 地名2（理由）
- 地名3（理由）

注意事項:
- 代表作は最大5作品
- 所縁の地は最大3箇所
- 理由は簡潔に（出生地、活動地、記念館など）
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
        収集したデータをDataFrameに変換
        
        Returns:
            pd.DataFrame: 整理されたデータ
        """
        print("データを整形中...")
        
        rows = []
        for author_data in self.authors_data:
            author_name = author_data['name']
            works = author_data['works']
            places = author_data['places']
            
            # 作品ごとに行を作成（作品がない場合は1行だけ）
            if not works:
                works = ['情報なし']
                
            for work in works:
                row = {
                    '作家名': author_name,
                    '代表作': work,
                    '所縁の地': ', '.join(places) if places else '情報なし'
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        print(f"DataFrame作成完了: {len(df)}行")
        return df
    
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
        DataFrameをGoogle Sheetsに保存
        
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
            
        try:
            print("Google Sheetsに保存中...")
            
            # 認証設定
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.google_credentials_path, scope)
            client = gspread.authorize(creds)
            
            # スプレッドシート作成
            sheet = client.create(sheet_name)
            worksheet = sheet.get_worksheet(0)
            
            # データ書き込み
            # ヘッダー
            worksheet.append_row(df.columns.tolist())
            
            # データ行
            for _, row in df.iterrows():
                worksheet.append_row(row.tolist())
            
            # 共有設定（誰でも閲覧可能）
            sheet.share('', perm_type='anyone', role='reader')
            
            print(f"Google Sheets保存完了: {sheet.url}")
            
        except Exception as e:
            print(f"Google Sheets保存エラー: {e}")
    
    def process_all_authors(self):
        """
        全体の処理を実行
        """
        print("=== 日本文豪情報収集システム開始 ===")
        
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
            
            # 初期抽出
            extracted_data = self.extract_works_and_places(author, content)
            
            # AI補完
            enhanced_data = self.enhance_with_ai(author, extracted_data)
            
            # データ保存
            self.authors_data.append({
                'name': author,
                'works': enhanced_data['works'],
                'places': enhanced_data['places']
            })
            
            # 進捗表示
            if i % 5 == 0:
                print(f"進捗: {i}/{len(authors)} 完了")
        
        # 3. データ整形と出力
        if self.authors_data:
            df = self.create_dataframe()
            
            # CSV出力
            self.save_to_csv(df)
            
            # Google Sheets出力
            if GSPREAD_AVAILABLE:
                self.save_to_google_sheets(df)
            else:
                print("Google Sheets出力をスキップしました（gspreadライブラリが利用できません）")
            
            print(f"\n=== 処理完了 ===")
            print(f"処理した作家数: {len(self.authors_data)}")
            print(f"出力行数: {len(df)}")
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
        
if __name__ == "__main__":
    collector = BungoCollector()
    collector.process_all_authors() 