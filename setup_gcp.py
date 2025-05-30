#!/usr/bin/env python3
"""
Google Cloud Platform 設定ガイド

プロジェクト作成からAPIの有効化、サービスアカウント作成まで
一連の手順を説明するスクリプト
"""

import webbrowser
import time

def print_step(step_num, title, description=""):
    """ステップを見やすく表示"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print("="*60)
    if description:
        print(description)
    print()

def wait_for_user():
    """ユーザーの準備ができるまで待機"""
    input("🔄 準備ができたらEnterキーを押してください...")

def main():
    print("🚀 Google Cloud Platform 設定ガイド")
    print("Google Sheets API連携のための設定を行います。")
    
    # Step 1: プロジェクト作成
    print_step(1, "プロジェクト作成", 
               "Google Cloud Consoleでプロジェクトを作成します。")
    
    print("📋 手順:")
    print("1. https://console.cloud.google.com/ にアクセス")
    print("2. 画面上部の「プロジェクト選択」をクリック")
    print("3. 「新しいプロジェクト」をクリック")
    print("4. プロジェクト名を入力（例: bungo-sheets-project）")
    print("5. 「作成」をクリック")
    
    print("\n🌐 Google Cloud Consoleを開きますか？")
    if input("y/N: ").lower() == 'y':
        webbrowser.open('https://console.cloud.google.com/')
    
    wait_for_user()
    
    # Step 2: APIの有効化
    print_step(2, "Google Sheets API & Google Drive APIの有効化",
               "プロジェクトで必要なAPIを有効化します。")
    
    print("📋 手順:")
    print("1. Google Cloud Consoleで作成したプロジェクトを選択")
    print("2. 左側メニューから「APIとサービス」→「ライブラリ」をクリック")
    print("3. 検索欄で「Google Sheets API」を検索し、有効化")
    print("4. 検索欄で「Google Drive API」を検索し、有効化")
    
    print("\n🌐 APIライブラリページを開きますか？")
    if input("y/N: ").lower() == 'y':
        webbrowser.open('https://console.cloud.google.com/apis/library')
    
    wait_for_user()
    
    # Step 3: サービスアカウント作成
    print_step(3, "サービスアカウントの作成",
               "APIにアクセスするためのサービスアカウントを作成します。")
    
    print("📋 手順:")
    print("1. Google Cloud Consoleで「IAMと管理」→「サービスアカウント」をクリック")
    print("2. 「サービスアカウントを作成」をクリック")
    print("3. 以下を入力:")
    print("   - サービスアカウント名: bungo-sheets-service")
    print("   - サービスアカウントID: 自動生成される")
    print("   - 説明: Bungo project Google Sheets access")
    print("4. 「作成して続行」をクリック")
    print("5. ロール: 「編集者」を選択")
    print("6. 「続行」→「完了」をクリック")
    
    print("\n🌐 サービスアカウントページを開きますか？")
    if input("y/N: ").lower() == 'y':
        webbrowser.open('https://console.cloud.google.com/iam-admin/serviceaccounts')
    
    wait_for_user()
    
    # Step 4: 認証キーのダウンロード
    print_step(4, "認証キーのダウンロード",
               "サービスアカウントのJSONキーファイルを作成・ダウンロードします。")
    
    print("📋 手順:")
    print("1. 作成したサービスアカウントをクリック")
    print("2. 「キー」タブをクリック")
    print("3. 「鍵を追加」→「新しい鍵を作成」をクリック")
    print("4. キータイプ: 「JSON」を選択")
    print("5. 「作成」をクリック")
    print("6. ダウンロードされたJSONファイルを `credentials.json` にリネーム")
    print("7. プロジェクトフォルダに配置")
    
    wait_for_user()
    
    # Step 5: セキュリティ確認
    print_step(5, "セキュリティ確認",
               "認証ファイルが正しく配置されているか確認します。")
    
    print("📋 確認事項:")
    print("✅ credentials.json がプロジェクトルートに配置されている")
    print("✅ ファイル権限が適切に設定されている")
    print("✅ .gitignore に credentials.json が追加されている")
    
    print("\n⚠️  セキュリティ注意事項:")
    print("- credentials.json は機密情報です")
    print("- GitHubなどにアップロードしないでください")
    print("- 必要に応じてアクセス権限を制限してください")
    
    wait_for_user()
    
    # 完了
    print("\n🎉 Google Cloud Platform 設定完了！")
    print("\n📝 次のステップ:")
    print("1. test_gsheets.py を実行してテスト")
    print("2. BungoCollectorでGoogle Sheets出力を実行")
    
    print("\n💡 ヒント:")
    print("- 問題が発生した場合は、APIが正しく有効化されているか確認")
    print("- サービスアカウントの権限が適切か確認")
    print("- credentials.json の内容が正しいか確認")

if __name__ == "__main__":
    main() 