#!/usr/bin/env python3
"""
Google Sheets接続テスト

credentials.jsonが正しく設定されているかを確認します。
"""

import os
import sys

def test_google_sheets_connection():
    """Google Sheets接続をテスト"""
    print("🧪 Google Sheets接続テスト開始")
    
    # 1. 認証ファイルの確認
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print(f"❌ 認証ファイルが見つかりません: {credentials_path}")
        print("\n📋 以下の手順で設定してください：")
        print("1. Google Cloud Console でプロジェクト作成")
        print("2. Google Sheets API・Google Drive API を有効化")
        print("3. サービスアカウント作成・JSON キーダウンロード")
        print("4. credentials.json として保存")
        return False
    
    print(f"✅ 認証ファイル確認: {credentials_path}")
    
    # 2. gspreadライブラリのテスト
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        print(f"✅ ライブラリ確認: gspread {gspread.__version__}")
    except ImportError as e:
        print(f"❌ ライブラリエラー: {e}")
        return False
    
    # 3. 認証テスト
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope)
        client = gspread.authorize(creds)
        print("✅ Google認証成功")
        
        # 4. テスト用スプレッドシート作成
        test_sheet_name = "bungo-test-sheet"
        try:
            sheet = client.create(test_sheet_name)
            worksheet = sheet.get_worksheet(0)
            
            # テストデータの書き込み
            worksheet.update('A1', 'テスト作家')
            worksheet.update('B1', 'テスト作品')
            worksheet.update('C1', 'テスト場所')
            
            worksheet.update('A2', '夏目漱石')
            worksheet.update('B2', '坊っちゃん')
            worksheet.update('C2', '東京')
            
            # 共有設定
            sheet.share('', perm_type='anyone', role='reader')
            
            print(f"✅ テストシート作成成功: {sheet.url}")
            print("🎯 Google Sheets連携が正常に動作しています！")
            
            # 後片付け
            try:
                client.del_spreadsheet(sheet.id)
                print("🧹 テストシートを削除しました")
            except:
                print("ℹ️  テストシートは手動で削除してください")
            
            return True
            
        except Exception as e:
            print(f"❌ シート操作エラー: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 認証エラー: {e}")
        print("\n🔧 対処方法：")
        print("- credentials.json の内容が正しいか確認")
        print("- Google Cloud Console でAPIが有効化されているか確認")
        print("- サービスアカウントに適切な権限があるか確認")
        return False

if __name__ == "__main__":
    success = test_google_sheets_connection()
    
    if success:
        print("\n🎉 Google Sheets設定完了！")
        print("メインシステムでGoogle Sheets出力が利用可能です。")
    else:
        print("\n❌ Google Sheets設定に問題があります。")
        print("上記のガイダンスに従って設定を確認してください。") 