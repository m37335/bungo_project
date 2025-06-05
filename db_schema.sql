-- 文豪作品地図システム データベーススキーマ
-- 仕様書 bungo_update_spec_draft01.md に基づく正規化3テーブル構造

-- 作者テーブル
CREATE TABLE IF NOT EXISTS authors (
    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    wikipedia_url TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 作品テーブル  
CREATE TABLE IF NOT EXISTS works (
    work_id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    wikipedia_url TEXT,
    aozora_url TEXT,
    publication_year INTEGER,
    genre TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES authors(author_id),
    UNIQUE(author_id, title)
);

-- 地名テーブル
CREATE TABLE IF NOT EXISTS places (
    place_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    place_name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    address TEXT,
    before_text TEXT,      -- 地名前の文章
    sentence TEXT,         -- 地名を含む文
    after_text TEXT,       -- 地名後の文章
    extraction_method TEXT, -- 'llm', 'ginza', 'regex'
    confidence REAL,       -- 抽出信頼度 0.0-1.0
    geocoded BOOLEAN DEFAULT FALSE,
    maps_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id),
    UNIQUE(work_id, place_name)
);

-- インデックス作成（検索高速化）
CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name);
CREATE INDEX IF NOT EXISTS idx_works_author_id ON works(author_id);
CREATE INDEX IF NOT EXISTS idx_works_title ON works(title);
CREATE INDEX IF NOT EXISTS idx_places_work_id ON places(work_id);
CREATE INDEX IF NOT EXISTS idx_places_name ON places(place_name);
CREATE INDEX IF NOT EXISTS idx_places_geocoded ON places(geocoded);

-- ビュー: 検索用統合ビュー
CREATE VIEW IF NOT EXISTS bungo_integrated AS
SELECT 
    a.name as author_name,
    w.title as work_title,
    p.place_name,
    p.latitude,
    p.longitude,
    p.address,
    p.before_text,
    p.sentence,
    p.after_text,
    p.extraction_method,
    p.confidence,
    p.geocoded,
    p.maps_url,
    a.author_id,
    w.work_id,
    p.place_id
FROM authors a
JOIN works w ON a.author_id = w.author_id  
JOIN places p ON w.work_id = p.work_id
ORDER BY a.name, w.title, p.place_name; 