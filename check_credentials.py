#!/usr/bin/env python3
"""
Google認証ファイル確認スクリプト

credentials.jsonが正しく配置されているかを確認します。
"""

import os
import json

def check_credentials_file():
    """credentials.jsonファイルの確認"""
    print("🔍 Google認証ファイルの確認")
    print("="*50)
    
    # ファイル存在確認
    credentials_path = "credentials.json"
    
    if not os.path.exists(credentials_path):
        print("❌ credentials.json が見つかりません")
        print(f"📁 現在のディレクトリ: {os.getcwd()}")
        print()
        print("📋 必要な手順:")
        print("1. Google Cloud Console → IAMと管理 → サービスアカウント")
        print("2. 作成したサービスアカウントをクリック")
        print("3. 「キー」タブ → 「鍵を追加」→ 「新しい鍵を作成」")
        print("4. JSON形式を選択して「作成」")
        print("5. ダウンロードされたファイルを credentials.json にリネーム")
        print("6. このフォルダに配置")
        return False
    
    print(f"✅ credentials.json が見つかりました")
    
    # ファイル内容確認
    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
        
        print(f"📄 ファイルサイズ: {os.path.getsize(credentials_path)} bytes")
        
        # 必要なキーの確認
        required_keys = [
            'type', 'project_id', 'private_key_id', 
            'private_key', 'client_email', 'client_id'
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in credentials:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ 必要なキーが不足: {missing_keys}")
            return False
        
        print("✅ 必要なキーがすべて含まれています")
        
        # 基本情報表示
        print()
        print("📊 認証情報の詳細:")
        print(f"  - タイプ: {credentials.get('type', 'N/A')}")
        print(f"  - プロジェクトID: {credentials.get('project_id', 'N/A')}")
        print(f"  - クライアントEmail: {credentials.get('client_email', 'N/A')}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSONファイルの形式が不正です: {e}")
        return False
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        return False

def show_next_steps():
    """次のステップを表示"""
    print()
    print("🎯 次のステップ:")
    print("1. python test_gsheets.py を実行してGoogle Sheets接続をテスト")
    print("2. 問題がなければBungoCollectorでGoogle Sheets出力が利用可能")

def main():
    success = check_credentials_file()
    
    if success:
        print()
        print("🎉 認証設定が正常に完了しました！")
        show_next_steps()
    else:
        print()
        print("❌ 認証設定に問題があります。")
        print("上記の手順に従って設定を完了してください。")

if __name__ == "__main__":
    main() 