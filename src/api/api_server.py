#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文豪ゆかり地図システム REST API
仕様書 bungo_update_spec_draft01.md S5章 API化に基づくFastAPI実装

OpenAPI仕様: s5_openapi_spec.yaml
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    raise ImportError("FastAPIライブラリが必要です: pip install fastapi uvicorn")

from db_utils import BungoDatabase
from gpt_relevance_service import GPTRelevanceService, RelevanceRequest
from export_geojson import GeoJSONExporter
from export_csv import CSVExporter, export_db_to_csv
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app初期化
app = FastAPI(
    title="文豪ゆかり地図システム API",
    description="""
文豪・作品・舞台（地名）の3階層データを管理し、
検索・可視化・GPT関連度判定機能を提供するREST API

**主要機能:**
- 作者・作品・地名の検索
- ジオコーディング・GeoJSONエクスポート
- GPT関連度判定（relevance≥0.8のみ可視化）
- データ収集・更新パイプライン
    """,
    version="1.0.0",
    contact={
        "name": "Bungo Map System",
        "email": "bungo-map@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバル依存関係
DATABASE_PATH = os.getenv('BUNGO_DB_PATH', 'test_ginza.db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_database() -> BungoDatabase:
    """データベース接続を取得"""
    return BungoDatabase("sqlite", DATABASE_PATH)

def get_gpt_service() -> GPTRelevanceService:
    """GPT関連度判定サービスを取得"""
    return GPTRelevanceService(OPENAI_API_KEY)

# Pydantic モデル定義

class ErrorResponse(BaseModel):
    error: Dict[str, str] = Field(..., description="エラー情報")

class HealthResponse(BaseModel):
    status: str = Field(..., description="ステータス")
    timestamp: datetime = Field(..., description="チェック時刻")
    version: str = Field(..., description="バージョン")

class AuthorSearchResponse(BaseModel):
    authors: List[Dict[str, Any]] = Field(..., description="検索された作者一覧")
    works: List[Dict[str, Any]] = Field(..., description="該当作者の作品一覧")
    execution_time: float = Field(..., description="実行時間（秒）")
    total_count: int = Field(..., description="総ヒット数")

class WorkSearchResponse(BaseModel):
    works: List[Dict[str, Any]] = Field(..., description="検索された作品一覧")
    places: List[Dict[str, Any]] = Field(..., description="該当作品の地名一覧")
    execution_time: float = Field(..., description="実行時間（秒）")
    total_count: int = Field(..., description="総ヒット数")

class PlaceSearchResponse(BaseModel):
    places: List[Dict[str, Any]] = Field(..., description="検索された地名一覧")
    authors: List[str] = Field(..., description="関連作者一覧")
    works: List[Dict[str, str]] = Field(..., description="関連作品一覧")
    execution_time: float = Field(..., description="実行時間（秒）")
    total_count: int = Field(..., description="総ヒット数")

class PlaceListResponse(BaseModel):
    places: List[Dict[str, Any]] = Field(..., description="地名一覧")
    pagination: Dict[str, Any] = Field(..., description="ページネーション情報")

class RelevanceRequestModel(BaseModel):
    place_name: str = Field(..., description="地名")
    sentence: str = Field(..., description="該当文")
    work_title: str = Field(..., description="作品タイトル")
    author_name: str = Field(..., description="作者名")
    context: Optional[str] = Field(None, description="追加文脈")

class RelevanceResponseModel(BaseModel):
    relevance_score: float = Field(..., description="関連度スコア")
    is_relevant: bool = Field(..., description="閾値（0.8）以上か")
    reasoning: str = Field(..., description="判定理由")
    execution_time: float = Field(..., description="実行時間（秒）")

class BatchRelevanceRequest(BaseModel):
    items: List[RelevanceRequestModel] = Field(..., max_items=100, description="一括判定対象")

class BatchRelevanceResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="判定結果一覧")
    total_count: int = Field(..., description="総件数")
    relevant_count: int = Field(..., description="関連度≥0.8の件数")
    execution_time: float = Field(..., description="実行時間（秒）")

class StatsResponse(BaseModel):
    authors_count: int = Field(..., description="作者数")
    works_count: int = Field(..., description="作品数")
    places_count: int = Field(..., description="地名数")
    geocoded_count: int = Field(..., description="ジオコーディング済み地名数")
    geocoded_rate: float = Field(..., description="ジオコーディング率（%）")
    relevant_places_count: Optional[int] = Field(None, description="関連度≥0.8の地名数")
    last_updated: datetime = Field(..., description="最終更新日時")

# =====================================
# API エンドポイント実装
# =====================================

@app.get("/health", response_model=HealthResponse, tags=["Admin"])
async def health_check():
    """ヘルスチェック"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(),
        version="1.0.0"
    )

@app.get("/stats", response_model=StatsResponse, tags=["Admin"])
async def get_stats(db: BungoDatabase = Depends(get_database)):
    """データベース統計取得"""
    try:
        stats = db.get_stats()
        db.close()
        
        return StatsResponse(
            authors_count=stats.get('authors_count', 0),
            works_count=stats.get('works_count', 0),
            places_count=stats.get('places_count', 0),
            geocoded_count=stats.get('geocoded_count', 0),
            geocoded_rate=stats.get('geocoded_rate', 0.0),
            last_updated=datetime.now()
        )
    except Exception as e:
        db.close()
        logger.error(f"統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "STATS_ERROR", "message": str(e)}})

# =====================================
# 検索エンドポイント
# =====================================

@app.get("/search/authors", response_model=AuthorSearchResponse, tags=["Search"])
async def search_authors(
    q: str = Query(..., description="検索クエリ（作者名）", min_length=1, max_length=100),
    limit: int = Query(10, description="最大結果数", ge=1, le=100),
    include_works: bool = Query(True, description="作品一覧を含むか"),
    db: BungoDatabase = Depends(get_database)
):
    """作者検索"""
    try:
        start_time = time.time()
        
        # 作者検索
        authors = db.search_authors(q)[:limit]
        
        # 作品一覧取得
        works = []
        if include_works:
            for author in authors:
                author_works = db.search_works("")  # 全作品取得
                works.extend([w for w in author_works if w.get('author_name') == author['name']])
        
        execution_time = time.time() - start_time
        db.close()
        
        return AuthorSearchResponse(
            authors=authors,
            works=works[:limit * 3],  # 作品は多めに表示
            execution_time=execution_time,
            total_count=len(authors)
        )
    except Exception as e:
        db.close()
        logger.error(f"作者検索エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "SEARCH_ERROR", "message": str(e)}})

@app.get("/search/works", response_model=WorkSearchResponse, tags=["Search"])
async def search_works(
    q: str = Query(..., description="検索クエリ（作品名）", min_length=1, max_length=100),
    limit: int = Query(10, description="最大結果数", ge=1, le=100),
    include_places: bool = Query(True, description="地名一覧を含むか"),
    db: BungoDatabase = Depends(get_database)
):
    """作品検索"""
    try:
        start_time = time.time()
        
        # 作品検索
        works = db.search_works(q)[:limit]
        
        # 地名一覧取得
        places = []
        if include_places:
            for work in works:
                work_places = db.search_places("")  # 全地名取得
                places.extend([p for p in work_places if p.get('work_title') == work['title']])
        
        execution_time = time.time() - start_time
        db.close()
        
        return WorkSearchResponse(
            works=works,
            places=places[:limit * 5],  # 地名は多めに表示
            execution_time=execution_time,
            total_count=len(works)
        )
    except Exception as e:
        db.close()
        logger.error(f"作品検索エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "SEARCH_ERROR", "message": str(e)}})

@app.get("/search/places", response_model=PlaceSearchResponse, tags=["Search"])
async def search_places(
    q: str = Query(..., description="検索クエリ（地名）", min_length=1, max_length=100),
    limit: int = Query(10, description="最大結果数", ge=1, le=100),
    include_reverse: bool = Query(True, description="作者・作品逆引きを含むか"),
    db: BungoDatabase = Depends(get_database)
):
    """地名検索"""
    try:
        start_time = time.time()
        
        # 地名検索
        places = db.search_places(q)[:limit]
        
        # 関連作者・作品の逆引き
        authors = set()
        works = set()
        
        if include_reverse:
            for place in places:
                if place.get('author_name'):
                    authors.add(place['author_name'])
                if place.get('work_title'):
                    works.add((place.get('author_name'), place['work_title']))
        
        execution_time = time.time() - start_time
        db.close()
        
        return PlaceSearchResponse(
            places=places,
            authors=list(authors),
            works=[{'author_name': author, 'title': work} for author, work in works],
            execution_time=execution_time,
            total_count=len(places)
        )
    except Exception as e:
        db.close()
        logger.error(f"地名検索エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "SEARCH_ERROR", "message": str(e)}})

# =====================================
# 地名詳細エンドポイント
# =====================================

@app.get("/places", response_model=PlaceListResponse, tags=["Places"])
async def get_places(
    author: Optional[str] = Query(None, description="作者名でフィルタ"),
    work: Optional[str] = Query(None, description="作品名でフィルタ"),
    geocoded_only: bool = Query(False, description="ジオコーディング済みのみ"),
    limit: int = Query(100, description="最大結果数", ge=1, le=1000),
    offset: int = Query(0, description="オフセット", ge=0),
    db: BungoDatabase = Depends(get_database)
):
    """地名一覧取得"""
    try:
        # フィルタ条件に応じて検索
        all_places = db.search_places("")  # 全地名取得
        
        # フィルタリング
        filtered_places = all_places
        
        if author:
            filtered_places = [p for p in filtered_places if author.lower() in p.get('author_name', '').lower()]
        
        if work:
            filtered_places = [p for p in filtered_places if work.lower() in p.get('work_title', '').lower()]
        
        if geocoded_only:
            filtered_places = [p for p in filtered_places if p.get('latitude') and p.get('longitude')]
        
        # ページネーション
        total = len(filtered_places)
        places = filtered_places[offset:offset + limit]
        
        db.close()
        
        return PlaceListResponse(
            places=places,
            pagination={
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        )
    except Exception as e:
        db.close()
        logger.error(f"地名一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "PLACES_ERROR", "message": str(e)}})

@app.get("/places/{place_id}", tags=["Places"])
async def get_place_detail(
    place_id: int = Path(..., description="地名ID"),
    db: BungoDatabase = Depends(get_database)
):
    """地名詳細取得"""
    try:
        # 地名詳細取得（実装は簡略化）
        places = db.search_places("")
        place = next((p for p in places if p.get('place_id') == place_id), None)
        
        db.close()
        
        if not place:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "地名が見つかりません"}})
        
        return place
    except HTTPException:
        db.close()
        raise
    except Exception as e:
        db.close()
        logger.error(f"地名詳細取得エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "PLACE_ERROR", "message": str(e)}})

# =====================================
# GPT関連度判定エンドポイント
# =====================================

@app.post("/gpt/relevance", response_model=RelevanceResponseModel, tags=["GPT"])
async def judge_relevance(
    request: RelevanceRequestModel = Body(...),
    gpt_service: GPTRelevanceService = Depends(get_gpt_service)
):
    """GPT関連度判定"""
    try:
        relevance_req = RelevanceRequest(
            place_name=request.place_name,
            sentence=request.sentence,
            work_title=request.work_title,
            author_name=request.author_name,
            context=request.context
        )
        
        response = gpt_service.judge_relevance(relevance_req)
        
        return RelevanceResponseModel(
            relevance_score=response.relevance_score,
            is_relevant=response.is_relevant,
            reasoning=response.reasoning,
            execution_time=response.execution_time
        )
    except Exception as e:
        logger.error(f"GPT関連度判定エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "GPT_ERROR", "message": str(e)}})

@app.post("/gpt/batch-relevance", response_model=BatchRelevanceResponse, tags=["GPT"])
async def judge_relevance_batch(
    request: BatchRelevanceRequest = Body(...),
    gpt_service: GPTRelevanceService = Depends(get_gpt_service)
):
    """GPT関連度一括判定"""
    try:
        start_time = time.time()
        
        relevance_requests = [
            RelevanceRequest(
                place_name=item.place_name,
                sentence=item.sentence,
                work_title=item.work_title,
                author_name=item.author_name,
                context=item.context
            )
            for item in request.items
        ]
        
        responses = gpt_service.judge_relevance_batch(relevance_requests)
        
        results = []
        for i, response in enumerate(responses):
            results.append({
                "index": i,
                "relevance_score": response.relevance_score,
                "is_relevant": response.is_relevant,
                "reasoning": response.reasoning,
                "execution_time": response.execution_time
            })
        
        relevant_count = sum(1 for r in responses if r.is_relevant)
        total_time = time.time() - start_time
        
        return BatchRelevanceResponse(
            results=results,
            total_count=len(results),
            relevant_count=relevant_count,
            execution_time=total_time
        )
    except Exception as e:
        logger.error(f"GPT一括関連度判定エラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "GPT_BATCH_ERROR", "message": str(e)}})

# =====================================
# GeoJSONエクスポート
# =====================================

@app.get("/export/geojson", tags=["Export"])
async def export_geojson(
    author: Optional[str] = Query(None, description="作者名でフィルタ"),
    work: Optional[str] = Query(None, description="作品名でフィルタ"),
    relevance_threshold: float = Query(0.8, description="GPT関連度判定の閾値", ge=0.0, le=1.0),
    db: BungoDatabase = Depends(get_database)
):
    """GeoJSONエクスポート"""
    try:
        # GeoJSONExporterを使用してエクスポート
        exporter = GeoJSONExporter("output")
        output_path = exporter.export_from_database(db, "api_export.geojson")
        
        db.close()
        
        if not output_path or not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail={"error": {"code": "EXPORT_ERROR", "message": "GeoJSONファイル生成に失敗しました"}})
        
        # ファイル内容を読み込んでJSONとして返す
        with open(output_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # application/geo+json で返す
        return JSONResponse(content=geojson_data, media_type="application/geo+json")
        
    except Exception as e:
        logger.error(f"GeoJSONエクスポートエラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "EXPORT_ERROR", "message": str(e)}})

# =====================================
# CSVエクスポート
# =====================================

@app.get("/export/csv", tags=["Export"])
async def export_csv(
    export_type: str = Query("combined", description="エクスポート種別", regex="^(all|authors|works|places|combined)$"),
    author: Optional[str] = Query(None, description="作者名でフィルタ"),
    work: Optional[str] = Query(None, description="作品名でフィルタ"),
    geocoded_only: bool = Query(False, description="ジオコーディング済みのみ（places時のみ）"),
    db: BungoDatabase = Depends(get_database)
):
    """データベース内容をCSVファイルにエクスポート"""
    try:
        db.close()  # 先にDBを閉じる
        
        # エクスポート実行
        results = export_db_to_csv(
            db_path=DATABASE_PATH,
            output_dir="output",
            export_type=export_type,
            author_filter=author,
            work_filter=work,
            geocoded_only=geocoded_only
        )
        
        # ファイル情報を取得
        file_info = []
        for key, filepath in results.items():
            file_size = os.path.getsize(filepath)
            file_info.append({
                "export_type": key,
                "filename": os.path.basename(filepath),
                "filepath": filepath,
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2)
            })
        
        return {
            "message": "CSVエクスポート完了",
            "export_type": export_type,
            "files": file_info,
            "filters": {
                "author": author,
                "work": work,
                "geocoded_only": geocoded_only
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"CSVエクスポートエラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "CSV_EXPORT_ERROR", "message": str(e)}})

@app.get("/export/csv/download/{filename}", tags=["Export"])
async def download_csv_file(filename: str = Path(..., description="ダウンロードするCSVファイル名")):
    """CSVファイルをダウンロード"""
    try:
        filepath = f"output/{filename}"
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail={"error": {"code": "FILE_NOT_FOUND", "message": "ファイルが見つかりません"}})
        
        from fastapi.responses import FileResponse
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="text/csv; charset=utf-8"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSVダウンロードエラー: {e}")
        raise HTTPException(status_code=500, detail={"error": {"code": "DOWNLOAD_ERROR", "message": str(e)}})

# =====================================
# サーバー起動関数
# =====================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """API サーバー起動"""
    try:
        import uvicorn
        logger.info(f"🚀 文豪ゆかり地図システム API サーバー起動: http://{host}:{port}")
        logger.info(f"📖 OpenAPI ドキュメント: http://{host}:{port}/docs")
        logger.info(f"📊 ReDoc ドキュメント: http://{host}:{port}/redoc")
        
        uvicorn.run("api_server:app", host=host, port=port, reload=reload)
    except ImportError:
        logger.error("uvicorn が必要です: pip install uvicorn")
        raise

if __name__ == "__main__":
    run_server() 