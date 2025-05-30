#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps連携デモスクリプト
詳細住所データをGoogle Mapsで表示
"""

import pandas as pd
import webbrowser
import urllib.parse
from typing import List, Dict
import time

class GoogleMapsConnector:
    """Google Maps連携機能"""
    
    def __init__(self, csv_file: str = "authors_googlemaps.csv"):
        """
        初期化
        
        Args:
            csv_file (str): Google Maps用CSVファイル
        """
        self.csv_file = csv_file
        self.maps_data = self._load_data()
    
    def _load_data(self) -> pd.DataFrame:
        """Google Maps用データを読み込み"""
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            print(f"📊 データ読み込み完了: {len(df)}件")
            return df
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {self.csv_file}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def search_by_author(self, author_name: str) -> List[Dict]:
        """
        作家名で検索
        
        Args:
            author_name (str): 作家名
            
        Returns:
            List[Dict]: 該当する地名情報
        """
        if self.maps_data.empty:
            return []
        
        filtered = self.maps_data[self.maps_data['作家名'].str.contains(author_name, na=False)]
        return filtered.to_dict('records')
    
    def search_by_type(self, place_type: str) -> List[Dict]:
        """
        地名種類で検索
        
        Args:
            place_type (str): 地名種類（記念館・文学施設、出生地など）
            
        Returns:
            List[Dict]: 該当する地名情報
        """
        if self.maps_data.empty:
            return []
        
        filtered = self.maps_data[self.maps_data['種類'].str.contains(place_type, na=False)]
        return filtered.to_dict('records')
    
    def get_maps_ready_places(self) -> List[Dict]:
        """Google Maps準備済みの地名を取得"""
        if self.maps_data.empty:
            return []
        
        filtered = self.maps_data[self.maps_data['Google Maps準備済み'] == '○']
        return filtered.to_dict('records')
    
    def create_maps_url(self, place_name: str, additional_query: str = "") -> str:
        """
        Google Maps URLを生成
        
        Args:
            place_name (str): 地名
            additional_query (str): 追加の検索クエリ
            
        Returns:
            str: Google Maps URL
        """
        query = f"{place_name} {additional_query}".strip()
        encoded_query = urllib.parse.quote(query)
        return f"https://www.google.com/maps/search/{encoded_query}"
    
    def open_in_maps(self, place_name: str, additional_query: str = ""):
        """
        Google Mapsでブラウザを開く
        
        Args:
            place_name (str): 地名
            additional_query (str): 追加の検索クエリ
        """
        url = self.create_maps_url(place_name, additional_query)
        print(f"🗺️ Google Mapsを開いています: {place_name}")
        print(f"   URL: {url}")
        webbrowser.open(url)
        
    def demo_author_tour(self, author_name: str):
        """
        作家の文学地めぐりデモ
        
        Args:
            author_name (str): 作家名
        """
        places = self.search_by_author(author_name)
        
        if not places:
            print(f"❌ {author_name}の地名情報が見つかりません")
            return
        
        print(f"\n🏃‍♂️ {author_name}の文学地めぐりを開始します！")
        print(f"   発見された地名: {len(places)}箇所")
        
        for i, place in enumerate(places, 1):
            print(f"\n📍 [{i}/{len(places)}] {place['地名']}")
            print(f"   種類: {place['種類']}")
            print(f"   Maps準備状況: {place['Google Maps準備済み']}")
            
            if place.get('文脈'):
                context = place['文脈'][:100] + "..." if len(place['文脈']) > 100 else place['文脈']
                print(f"   文脈: {context}")
            
            # Google Mapsで開くか確認
            response = input(f"   🗺️ Google Mapsで開きますか？ (y/n/q): ").lower()
            
            if response == 'q':
                print("   📋 文学地めぐりを終了します")
                break
            elif response == 'y':
                additional_query = f"{author_name} 文学" if place['種類'] != '記念館・文学施設' else ""
                self.open_in_maps(place['地名'], additional_query)
                time.sleep(2)  # ブラウザが開くまで待機
        
        print(f"\n🎉 {author_name}の文学地めぐり完了！")
    
    def create_literary_map_html(self, output_file: str = "literary_map.html"):
        """
        文学地図のHTMLファイルを生成
        
        Args:
            output_file (str): 出力ファイル名
        """
        if self.maps_data.empty:
            print("❌ データがありません")
            return
        
        html_content = self._generate_html_template()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"🗺️ 文学地図HTML作成完了: {output_file}")
            
            # ブラウザで開く
            import os
            file_path = os.path.abspath(output_file)
            webbrowser.open(f"file://{file_path}")
            
        except Exception as e:
            print(f"❌ HTMLファイル作成エラー: {e}")
    
    def _generate_html_template(self) -> str:
        """HTML地図テンプレートを生成"""
        places_data = []
        
        for _, row in self.maps_data.iterrows():
            if row['Google Maps準備済み'] == '○':
                place_data = {
                    'name': row['地名'],
                    'author': row['作家名'],
                    'type': row['種類'],
                    'query': row['検索用地名'],
                    'maps_url': self.create_maps_url(row['地名'])
                }
                places_data.append(place_data)
        
        # JavaScriptで使用するデータを生成
        js_data = str(places_data).replace("'", '"')
        
        html_template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日本文豪文学地図</title>
    <style>
        body {{
            font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        .place-card {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin: 15px 0;
            padding: 20px;
            background: #fafafa;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .place-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .place-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .author-name {{
            color: #666;
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        .place-type {{
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        .maps-button {{
            background: #4285f4;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: background-color 0.2s;
        }}
        .maps-button:hover {{
            background: #3367d6;
        }}
        .stats {{
            background: #e8f5e8;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .filter-controls {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f0f0f0;
            border-radius: 8px;
        }}
        .filter-button {{
            background: #757575;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .filter-button.active {{
            background: #2196f3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 日本文豪文学地図 🗺️</h1>
            <p>文豪ゆかりの地をGoogle Mapsで探訪しよう</p>
        </div>
        
        <div class="content">
            <div class="stats">
                <h3>📊 統計情報</h3>
                <p>総地名数: <strong>{len(places_data)}</strong>箇所</p>
                <p>Google Maps準備済み: <strong>{len([p for p in places_data])}</strong>箇所</p>
            </div>
            
            <div class="filter-controls">
                <h3>🔍 フィルター</h3>
                <button class="filter-button active" onclick="filterPlaces('all')">すべて</button>
                <button class="filter-button" onclick="filterPlaces('記念館・文学施設')">記念館・文学施設</button>
                <button class="filter-button" onclick="filterPlaces('出生地')">出生地</button>
                <button class="filter-button" onclick="filterPlaces('居住地')">居住地</button>
                <button class="filter-button" onclick="filterPlaces('墓所')">墓所</button>
            </div>
            
            <div id="places-container">
                <!-- 地名カードがここに表示されます -->
            </div>
        </div>
    </div>

    <script>
        const placesData = {js_data};
        
        function renderPlaces(data) {{
            const container = document.getElementById('places-container');
            container.innerHTML = '';
            
            data.forEach(place => {{
                const card = document.createElement('div');
                card.className = 'place-card';
                card.innerHTML = `
                    <div class="place-name">${{place.name}}</div>
                    <div class="author-name">📖 ${{place.author}}</div>
                    <span class="place-type">${{place.type}}</span>
                    <br>
                    <a href="${{place.maps_url}}" target="_blank" class="maps-button">
                        🗺️ Google Mapsで開く
                    </a>
                `;
                container.appendChild(card);
            }});
        }}
        
        function filterPlaces(type) {{
            // ボタンのアクティブ状態を更新
            document.querySelectorAll('.filter-button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            // データをフィルタリング
            let filteredData = placesData;
            if (type !== 'all') {{
                filteredData = placesData.filter(place => place.type.includes(type));
            }}
            
            renderPlaces(filteredData);
        }}
        
        // 初期表示
        renderPlaces(placesData);
    </script>
</body>
</html>
        """
        
        return html_template
    
    def generate_summary_report(self) -> Dict:
        """統計レポートを生成"""
        if self.maps_data.empty:
            return {}
        
        total_places = len(self.maps_data)
        maps_ready = len(self.maps_data[self.maps_data['Google Maps準備済み'] == '○'])
        
        # 作家別統計
        author_stats = self.maps_data['作家名'].value_counts().to_dict()
        
        # 種類別統計
        type_stats = self.maps_data['種類'].value_counts().to_dict()
        
        # Maps準備率
        maps_ready_rate = (maps_ready / total_places * 100) if total_places > 0 else 0
        
        return {
            '総地名数': total_places,
            'Maps準備済み': maps_ready,
            'Maps準備率': f"{maps_ready_rate:.1f}%",
            '作家別統計': author_stats,
            '種類別統計': type_stats
        }

def main():
    """メイン実行関数"""
    print("🗺️ Google Maps連携デモ")
    print("=" * 40)
    
    # Google Mapsコネクター初期化
    connector = GoogleMapsConnector()
    
    if connector.maps_data.empty:
        print("❌ データが読み込めませんでした")
        return
    
    while True:
        print("\n📋 メニュー:")
        print("1. 作家名で検索")
        print("2. 記念館・文学施設一覧")
        print("3. 作家の文学地めぐり")
        print("4. 文学地図HTML作成")
        print("5. 統計レポート")
        print("6. 終了")
        
        choice = input("\n選択してください (1-6): ").strip()
        
        if choice == '1':
            author = input("作家名を入力してください: ").strip()
            places = connector.search_by_author(author)
            
            if places:
                print(f"\n📍 {author}の関連地名: {len(places)}件")
                for i, place in enumerate(places, 1):
                    print(f"{i}. {place['地名']} ({place['種類']}) - {place['Google Maps準備済み']}")
            else:
                print(f"❌ {author}の地名情報が見つかりません")
        
        elif choice == '2':
            museums = connector.search_by_type("記念館・文学施設")
            print(f"\n🏛️ 記念館・文学施設: {len(museums)}件")
            for i, place in enumerate(museums[:10], 1):  # 最大10件表示
                print(f"{i}. {place['地名']} ({place['作家名']})")
        
        elif choice == '3':
            author = input("文学地めぐりしたい作家名を入力してください: ").strip()
            connector.demo_author_tour(author)
        
        elif choice == '4':
            connector.create_literary_map_html()
        
        elif choice == '5':
            report = connector.generate_summary_report()
            print("\n📊 統計レポート:")
            for key, value in report.items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    for k, v in list(value.items())[:5]:  # 上位5件
                        print(f"  {k}: {v}")
                else:
                    print(f"{key}: {value}")
        
        elif choice == '6':
            print("👋 終了します")
            break
        
        else:
            print("❌ 無効な選択です")

if __name__ == "__main__":
    main() 