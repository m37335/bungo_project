#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
著名文豪データ追加スクリプト
夏目漱石に加えて14名の日本文豪をデータベースに追加
"""

import sqlite3
from typing import List, Dict
from db_utils import BungoDatabase

def get_famous_authors() -> List[Dict]:
    """著名な日本文豪15名のデータ"""
    authors = [
        {
            "name": "夏目漱石",
            "birth_year": 1867,
            "death_year": 1916,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/夏目漱石"
        },
        {
            "name": "芥川龍之介", 
            "birth_year": 1892,
            "death_year": 1927,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/芥川龍之介"
        },
        {
            "name": "太宰治",
            "birth_year": 1909,
            "death_year": 1948,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/太宰治"
        },
        {
            "name": "川端康成",
            "birth_year": 1899,
            "death_year": 1972,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/川端康成"
        },
        {
            "name": "三島由紀夫",
            "birth_year": 1925,
            "death_year": 1970,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/三島由紀夫"
        },
        {
            "name": "森鴎外",
            "birth_year": 1862,
            "death_year": 1922,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/森鴎外"
        },
        {
            "name": "樋口一葉",
            "birth_year": 1872,
            "death_year": 1896,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/樋口一葉"
        },
        {
            "name": "宮沢賢治",
            "birth_year": 1896,
            "death_year": 1933,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/宮沢賢治"
        },
        {
            "name": "与謝野晶子",
            "birth_year": 1878,
            "death_year": 1942,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/与謝野晶子"
        },
        {
            "name": "正岡子規",
            "birth_year": 1867,
            "death_year": 1902,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/正岡子規"
        },
        {
            "name": "石川啄木",
            "birth_year": 1886,
            "death_year": 1912,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/石川啄木"
        },
        {
            "name": "中島敦",
            "birth_year": 1909,
            "death_year": 1942,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/中島敦"
        },
        {
            "name": "谷崎潤一郎",
            "birth_year": 1886,
            "death_year": 1965,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/谷崎潤一郎"
        },
        {
            "name": "志賀直哉",
            "birth_year": 1883,
            "death_year": 1971,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/志賀直哉"
        },
        {
            "name": "武者小路実篤",
            "birth_year": 1885,
            "death_year": 1976,
            "wikipedia_url": "https://ja.wikipedia.org/wiki/武者小路実篤"
        }
    ]
    return authors

def get_sample_works() -> List[Dict]:
    """各作者の代表作品データ"""
    works = [
        # 夏目漱石
        {"author_name": "夏目漱石", "title": "吾輩は猫である", "publication_year": 1905, "genre": "小説"},
        {"author_name": "夏目漱石", "title": "坊っちゃん", "publication_year": 1906, "genre": "小説"},
        {"author_name": "夏目漱石", "title": "こころ", "publication_year": 1914, "genre": "小説"},
        
        # 芥川龍之介
        {"author_name": "芥川龍之介", "title": "羅生門", "publication_year": 1915, "genre": "短編小説"},
        {"author_name": "芥川龍之介", "title": "蜘蛛の糸", "publication_year": 1918, "genre": "短編小説"},
        {"author_name": "芥川龍之介", "title": "地獄変", "publication_year": 1918, "genre": "短編小説"},
        
        # 太宰治
        {"author_name": "太宰治", "title": "人間失格", "publication_year": 1948, "genre": "小説"},
        {"author_name": "太宰治", "title": "斜陽", "publication_year": 1947, "genre": "小説"},
        {"author_name": "太宰治", "title": "津軽", "publication_year": 1944, "genre": "紀行文"},
        
        # 川端康成
        {"author_name": "川端康成", "title": "雪国", "publication_year": 1937, "genre": "小説"},
        {"author_name": "川端康成", "title": "伊豆の踊子", "publication_year": 1926, "genre": "短編小説"},
        {"author_name": "川端康成", "title": "千羽鶴", "publication_year": 1952, "genre": "小説"},
        
        # 三島由紀夫
        {"author_name": "三島由紀夫", "title": "金閣寺", "publication_year": 1956, "genre": "小説"},
        {"author_name": "三島由紀夫", "title": "仮面の告白", "publication_year": 1949, "genre": "小説"},
        {"author_name": "三島由紀夫", "title": "潮騒", "publication_year": 1954, "genre": "小説"},
        
        # 森鴎外
        {"author_name": "森鴎外", "title": "舞姫", "publication_year": 1890, "genre": "短編小説"},
        {"author_name": "森鴎外", "title": "高瀬舟", "publication_year": 1916, "genre": "短編小説"},
        {"author_name": "森鴎外", "title": "阿部一族", "publication_year": 1913, "genre": "歴史小説"},
        
        # 樋口一葉
        {"author_name": "樋口一葉", "title": "たけくらべ", "publication_year": 1895, "genre": "小説"},
        {"author_name": "樋口一葉", "title": "にごりえ", "publication_year": 1895, "genre": "短編小説"},
        {"author_name": "樋口一葉", "title": "十三夜", "publication_year": 1895, "genre": "短編小説"},
        
        # 宮沢賢治
        {"author_name": "宮沢賢治", "title": "銀河鉄道の夜", "publication_year": 1934, "genre": "童話"},
        {"author_name": "宮沢賢治", "title": "注文の多い料理店", "publication_year": 1924, "genre": "童話"},
        {"author_name": "宮沢賢治", "title": "風の又三郎", "publication_year": 1934, "genre": "童話"},
        
        # 与謝野晶子
        {"author_name": "与謝野晶子", "title": "みだれ髪", "publication_year": 1901, "genre": "歌集"},
        {"author_name": "与謝野晶子", "title": "小扇", "publication_year": 1904, "genre": "歌集"},
        
        # 正岡子規
        {"author_name": "正岡子規", "title": "病床六尺", "publication_year": 1902, "genre": "随筆"},
        {"author_name": "正岡子規", "title": "墨汁一滴", "publication_year": 1901, "genre": "随筆"},
        
        # 石川啄木
        {"author_name": "石川啄木", "title": "一握の砂", "publication_year": 1910, "genre": "歌集"},
        {"author_name": "石川啄木", "title": "悲しき玩具", "publication_year": 1912, "genre": "歌集"},
        
        # 中島敦
        {"author_name": "中島敦", "title": "山月記", "publication_year": 1942, "genre": "短編小説"},
        {"author_name": "中島敦", "title": "李陵", "publication_year": 1943, "genre": "短編小説"},
        
        # 谷崎潤一郎
        {"author_name": "谷崎潤一郎", "title": "細雪", "publication_year": 1948, "genre": "小説"},
        {"author_name": "谷崎潤一郎", "title": "春琴抄", "publication_year": 1933, "genre": "小説"},
        
        # 志賀直哉
        {"author_name": "志賀直哉", "title": "暗夜行路", "publication_year": 1937, "genre": "小説"},
        {"author_name": "志賀直哉", "title": "城の崎にて", "publication_year": 1917, "genre": "短編小説"},
        
        # 武者小路実篤
        {"author_name": "武者小路実篤", "title": "お目出たき人", "publication_year": 1911, "genre": "小説"},
        {"author_name": "武者小路実篤", "title": "友情", "publication_year": 1919, "genre": "小説"}
    ]
    return works

def add_authors_to_db(db_path: str = "test_ginza.db"):
    """データベースに作者データを追加"""
    print("🚀 文豪データベース拡張開始")
    print("=" * 50)
    
    # データベース接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 既存作者確認
        cursor.execute("SELECT COUNT(*) FROM authors")
        existing_count = cursor.fetchone()[0]
        print(f"既存作者数: {existing_count}名")
        
        # 新規作者追加
        authors = get_famous_authors()
        added_authors = 0
        
        for author in authors:
            # 重複チェック
            cursor.execute("SELECT author_id FROM authors WHERE name = ?", (author["name"],))
            if cursor.fetchone():
                print(f"   ⚠️ 既存: {author['name']} (スキップ)")
                continue
            
            # 作者追加
            cursor.execute("""
                INSERT INTO authors (name, birth_year, death_year, wikipedia_url)
                VALUES (?, ?, ?, ?)
            """, (
                author["name"],
                author["birth_year"],
                author["death_year"],
                author["wikipedia_url"]
            ))
            added_authors += 1
            print(f"   ✅ 追加: {author['name']} ({author['birth_year']}-{author['death_year']})")
        
        # 作品データ追加
        works = get_sample_works()
        added_works = 0
        
        print(f"\n📚 作品データ追加:")
        for work in works:
            # 作者IDを取得
            cursor.execute("SELECT author_id FROM authors WHERE name = ?", (work["author_name"],))
            author_row = cursor.fetchone()
            if not author_row:
                print(f"   ❌ 作者未発見: {work['author_name']}")
                continue
            
            author_id = author_row[0]
            
            # 重複チェック
            cursor.execute("SELECT work_id FROM works WHERE title = ? AND author_id = ?", (work["title"], author_id))
            if cursor.fetchone():
                continue
            
            # 作品追加
            cursor.execute("""
                INSERT INTO works (author_id, title, publication_year, genre)
                VALUES (?, ?, ?, ?)
            """, (
                author_id,
                work["title"],
                work["publication_year"],
                work["genre"]
            ))
            added_works += 1
            print(f"   ✅ {work['author_name']}: {work['title']} ({work['publication_year']})")
        
        # コミット
        conn.commit()
        
        # 最終統計
        cursor.execute("SELECT COUNT(*) FROM authors")
        total_authors = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM works")
        total_works = cursor.fetchone()[0]
        
        print("=" * 50)
        print(f"🎉 データベース拡張完了!")
        print(f"   新規作者: {added_authors}名")
        print(f"   新規作品: {added_works}件")
        print(f"   総作者数: {total_authors}名")
        print(f"   総作品数: {total_works}件")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_data(db_path: str = "test_ginza.db"):
    """追加されたデータの確認"""
    print("\n🔍 データ確認:")
    
    db = BungoDatabase("sqlite", db_path)
    
    # 作者一覧
    authors = db.search_authors("")
    print(f"\n📚 登録作者一覧 ({len(authors)}名):")
    for i, author in enumerate(authors, 1):
        birth_death = f"({author.get('birth_year', '?')}-{author.get('death_year', '?')})"
        print(f"   {i:2d}. {author['name']} {birth_death}")
    
    # 作品統計
    works = db.search_works("")
    print(f"\n📖 作品統計 ({len(works)}件):")
    
    # 作者別作品数
    author_works = {}
    for work in works:
        author_name = work.get('author_name', '不明')
        author_works[author_name] = author_works.get(author_name, 0) + 1
    
    for author, count in sorted(author_works.items()):
        print(f"   {author}: {count}件")
    
    db.close()

def main():
    """メイン実行"""
    success = add_authors_to_db()
    
    if success:
        verify_data()
        print(f"\n💡 次のステップ:")
        print(f"   1. CSVエクスポートのテスト: python3 export_csv.py --type all")
        print(f"   2. データベース内容確認: python3 test_csv_export.py")
        print(f"   3. API サーバー起動: python3 api_server.py")
    else:
        print(f"\n❌ データ追加に失敗しました。")

if __name__ == "__main__":
    main() 