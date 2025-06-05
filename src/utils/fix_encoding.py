#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文字化け解決ユーティリティ
ターミナルでの日本語表示問題を解決
"""

import os
import sys
import locale
from db_utils import BungoDatabase

def fix_terminal_encoding():
    """ターミナルエンコーディングを修正"""
    # 環境変数設定
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LC_ALL'] = 'ja_JP.UTF-8'
    os.environ['LANG'] = 'ja_JP.UTF-8'
    
    # Python内部エンコーディング設定
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    print("✅ エンコーディング設定完了")
    print(f"   システムエンコーディング: {sys.getdefaultencoding()}")
    print(f"   標準出力エンコーディング: {sys.stdout.encoding}")
    
    # ロケール確認
    try:
        current_locale = locale.getlocale()
        print(f"   現在のロケール: {current_locale}")
    except Exception as e:
        print(f"   ロケール取得エラー: {e}")

def test_japanese_display():
    """日本語表示テスト"""
    print("\n🗾 日本語表示テスト:")
    
    test_strings = [
        "夏目漱石",
        "草枕",
        "文豪ゆかり地図システム", 
        "だんだら峠",
        "GPT関連度判定",
        "ジオコーディング"
    ]
    
    for i, text in enumerate(test_strings, 1):
        print(f"   {i}. {text}")

def check_database_encoding():
    """データベースエンコーディング確認"""
    print("\n📊 データベース内容確認:")
    
    try:
        db = BungoDatabase("sqlite", "test_ginza.db")
        
        # 作者データ
        authors = db.search_authors("")
        if authors:
            print(f"   作者: {authors[0]['name']}")
        
        # 作品データ
        works = db.search_works("")
        if works:
            print(f"   作品: {works[0]['title']}")
        
        # 地名データ（最初の3件）
        places = db.search_places("")[:3]
        print(f"   地名一覧:")
        for place in places:
            print(f"     - {place['place_name']}")
            if place.get('sentence'):
                sentence = place['sentence'][:30]
                print(f"       文: {sentence}...")
        
        db.close()
        print("✅ データベース内容正常")
        
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")

def fix_output_files():
    """出力ファイルのエンコーディング修正"""
    print("\n📁 出力ファイル確認:")
    
    files_to_check = [
        "output/bungo_places_s3.geojson",
        "output/bungo_analysis_s3.csv", 
        "geocode_cache.json"
    ]
    
    for filepath in files_to_check:
        try:
            # UTF-8で読み込み
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(100)  # 最初の100文字
                print(f"   ✅ {filepath}: UTF-8読み込み成功")
                # 日本語が含まれているかチェック
                if any(ord(c) > 127 for c in content):
                    print(f"      日本語文字含有: あり")
                
        except UnicodeDecodeError as e:
            print(f"   ❌ {filepath}: UTF-8エラー - {e}")
            
            # 他のエンコーディングで試す
            encodings = ['shift_jis', 'euc-jp', 'iso-2022-jp']
            for enc in encodings:
                try:
                    with open(filepath, 'r', encoding=enc) as f:
                        content = f.read(100)
                        print(f"      💡 {enc}で読み込み成功")
                        
                        # UTF-8で再保存
                        backup_path = f"{filepath}.backup"
                        os.rename(filepath, backup_path)
                        
                        with open(backup_path, 'r', encoding=enc) as fin:
                            with open(filepath, 'w', encoding='utf-8') as fout:
                                fout.write(fin.read())
                        
                        print(f"      ✅ UTF-8に変換完了（バックアップ: {backup_path}）")
                        break
                        
                except Exception:
                    continue
        
        except FileNotFoundError:
            print(f"   ⚠️ {filepath}: ファイルなし")

def show_recommendations():
    """文字化け対策の推奨設定"""
    print("\n💡 文字化け対策推奨設定:")
    print("1. ターミナル設定:")
    print("   export LANG=ja_JP.UTF-8")
    print("   export LC_ALL=ja_JP.UTF-8") 
    print("   export PYTHONIOENCODING=utf-8")
    
    print("\n2. .zshrc/.bashrcに追加:")
    print("   echo 'export LANG=ja_JP.UTF-8' >> ~/.zshrc")
    print("   echo 'export LC_ALL=ja_JP.UTF-8' >> ~/.zshrc")
    print("   echo 'export PYTHONIOENCODING=utf-8' >> ~/.zshrc")
    
    print("\n3. Python実行時:")
    print("   python3 -c 'import sys; print(sys.stdout.encoding)'")
    
    print("\n4. Visual Studio Code設定:")
    print("   settings.json に追加:")
    print("   \"terminal.integrated.env.osx\": {")
    print("     \"LANG\": \"ja_JP.UTF-8\",")
    print("     \"LC_ALL\": \"ja_JP.UTF-8\"")
    print("   }")

def main():
    """メイン実行"""
    print("🔧 文豪ゆかり地図システム - 文字化け解決ツール")
    print("=" * 50)
    
    # エンコーディング修正
    fix_terminal_encoding()
    
    # 日本語表示テスト
    test_japanese_display()
    
    # データベース確認
    check_database_encoding()
    
    # 出力ファイル確認
    fix_output_files()
    
    # 推奨設定表示
    show_recommendations()
    
    print("\n🎉 文字化け対策完了！")

if __name__ == "__main__":
    main() 