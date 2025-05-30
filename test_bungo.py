#!/usr/bin/env python3
"""
日本の文豪情報収集システム テスト版

少数の文豪でシステムの動作確認を行います。
本格運用前にこのスクリプトで動作確認することを推奨します。
"""

import os
import sys
from bungo_collector import BungoCollector

class TestBungoCollector(BungoCollector):
    """テスト用の文豪収集システム"""
    
    def __init__(self):
        super().__init__()
        # テスト用に処理数を制限
        self.max_authors = 5
        
    def get_test_authors_list(self):
        """
        テスト用の文豪リスト（少数の有名作家）
        
        Returns:
            List[str]: テスト用文豪名のリスト
        """
        print("テスト用文豪一覧を準備中...")
        
        # テスト用の有名文豪（確実にWikipediaページがあるもの）
        test_authors = [
            "夏目漱石",
            "芥川龍之介", 
            "太宰治",
            "川端康成",
            "宮沢賢治"
        ]
        
        print(f"テスト対象: {len(test_authors)}名の文豪")
        for i, author in enumerate(test_authors, 1):
            print(f"  {i}. {author}")
            
        return test_authors
    
    def test_wikipedia_access(self):
        """Wikipedia接続テスト"""
        print("\n=== Wikipedia接続テスト ===")
        
        test_author = "夏目漱石"
        content = self.get_wikipedia_content(test_author)
        
        if content:
            print(f"✅ Wikipedia接続成功")
            print(f"取得した本文の長さ: {len(content)}文字")
            print(f"本文の一部: {content[:100]}...")
            return True
        else:
            print(f"❌ Wikipedia接続失敗")
            return False
    
    def test_extraction(self):
        """情報抽出テスト"""
        print("\n=== 情報抽出テスト ===")
        
        test_author = "夏目漱石"
        content = self.get_wikipedia_content(test_author)
        
        if content:
            extracted = self.extract_works_and_places(test_author, content)
            print(f"✅ 情報抽出成功")
            print(f"抽出された作品: {extracted['works']}")
            print(f"抽出された場所: {extracted['places']}")
            return True
        else:
            print(f"❌ 情報抽出失敗（Wikipedia取得エラー）")
            return False
    
    def test_ai_enhancement(self):
        """AI補完テスト"""
        print("\n=== AI補完テスト ===")
        
        if not self.openai_api_key:
            print("⚠️  OpenAI APIキーが設定されていません。AI補完をスキップします。")
            return True
            
        test_data = {
            "works": ["坊っちゃん", "こころ"],
            "places": ["東京", "愛媛"]
        }
        
        enhanced = self.enhance_with_ai("夏目漱石", test_data)
        
        if enhanced:
            print(f"✅ AI補完成功")
            print(f"補完された作品: {enhanced['works']}")
            print(f"補完された場所: {enhanced['places']}")
            return True
        else:
            print(f"❌ AI補完失敗")
            return False
    
    def test_data_processing(self):
        """データ処理テスト"""
        print("\n=== データ処理テスト ===")
        
        # テストデータを用意
        self.authors_data = [
            {
                'name': 'テスト作家1',
                'works': ['作品A', '作品B'],
                'places': ['東京', '大阪']
            },
            {
                'name': 'テスト作家2', 
                'works': ['作品C'],
                'places': ['京都']
            }
        ]
        
        try:
            df = self.create_dataframe()
            print(f"✅ DataFrame作成成功")
            print(f"データフレーム形状: {df.shape}")
            print("データフレーム内容:")
            print(df.to_string())
            
            # CSV保存テスト
            test_filename = "test_authors.csv"
            self.save_to_csv(df, test_filename)
            
            if os.path.exists(test_filename):
                print(f"✅ CSV保存成功: {test_filename}")
                # テストファイルを削除
                os.remove(test_filename)
                print(f"テストファイルを削除しました")
            else:
                print(f"❌ CSV保存失敗")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ データ処理エラー: {e}")
            return False
    
    def run_full_test(self):
        """フルテストの実行"""
        print("=== 日本文豪情報収集システム フルテスト開始 ===")
        
        # 作家一覧取得
        authors = self.get_test_authors_list()
        
        # 各作家の情報収集（1名のみ）
        test_author = authors[0]
        print(f"\n[フルテスト] 処理中: {test_author}")
        
        # Wikipedia本文取得
        content = self.get_wikipedia_content(test_author)
        if not content:
            print(f"❌ フルテスト失敗: Wikipedia取得エラー")
            return False
        
        # 初期抽出
        extracted_data = self.extract_works_and_places(test_author, content)
        
        # AI補完
        enhanced_data = self.enhance_with_ai(test_author, extracted_data)
        
        # データ保存
        self.authors_data = [{
            'name': test_author,
            'works': enhanced_data['works'],
            'places': enhanced_data['places']
        }]
        
        # データ整形と出力
        df = self.create_dataframe()
        
        # CSV出力
        test_filename = "test_authors_full.csv"
        self.save_to_csv(df, test_filename)
        
        print(f"\n=== フルテスト完了 ===")
        print(f"✅ 処理完了: {test_author}")
        print(f"✅ 出力ファイル: {test_filename}")
        print(f"作品数: {len(enhanced_data['works'])}")
        print(f"場所数: {len(enhanced_data['places'])}")
        
        # 結果表示
        print("\n最終結果:")
        print(df.to_string())
        
        return True

def main():
    """メイン関数"""
    print("日本の文豪情報収集システム - テストモード")
    print("=" * 50)
    
    # テストインスタンス作成
    test_collector = TestBungoCollector()
    
    # 各種テストの実行
    tests = [
        ("Wikipedia接続", test_collector.test_wikipedia_access),
        ("情報抽出", test_collector.test_extraction),
        ("AI補完", test_collector.test_ai_enhancement),
        ("データ処理", test_collector.test_data_processing),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name}テスト {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}テストでエラー: {e}")
            results.append((test_name, False))
    
    # テスト結果サマリー
    print(f"\n{'='*20} テスト結果サマリー {'='*20}")
    all_passed = True
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    # フルテスト実行の判断
    if all_passed:
        print(f"\n全テストが成功しました！")
        
        response = input("\nフルテストを実行しますか？(y/N): ")
        if response.lower() in ['y', 'yes']:
            test_collector.run_full_test()
        else:
            print("フルテストをスキップしました。")
    else:
        print(f"\n一部のテストが失敗しました。設定を確認してください。")
    
    print(f"\nテスト終了")

if __name__ == "__main__":
    main() 