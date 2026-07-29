import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query
from src.api.schemas import HistoryItemResponse
from src.infrastructure.database.cache_repo import (
    get_analysis_history,
    get_analysis_report_by_id,
    delete_analysis_report
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["History"])

@router.get("/history", response_model=List[HistoryItemResponse])
async def list_history(limit: int = Query(15, ge=1, le=100)):
    """
    Returns recent investment analysis reports saved in SQLite database.
    """
    try:
        items = get_analysis_history(limit=limit)
        results = []
        for item in items:
            results.append(HistoryItemResponse(
                id=item["id"],
                ticker=item["ticker"],
                market=item.get("market", "VN"),
                analysis_mode=item.get("analysis_mode", "full"),
                recommendation=item.get("recommendation", "HOLD"),
                created_at=str(item.get("created_at", "")),
                report_markdown=""
            ))
        return results
    except Exception as e:
        logger.error(f"Failed to fetch analysis history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@router.get("/history/{history_id}", response_model=HistoryItemResponse)
async def get_history_detail(history_id: int):
    """
    Retrieves full details and Markdown report of a specific historical analysis.
    """
    try:
        report = get_analysis_report_by_id(history_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"History record with ID {history_id} not found.")
            
        return HistoryItemResponse(
            id=report["id"],
            ticker=report["ticker"],
            market=report.get("market", "VN"),
            analysis_mode=report.get("analysis_mode", "full"),
            recommendation=report.get("recommendation", "HOLD"),
            created_at=str(report.get("created_at", "")),
            report_markdown=report.get("report_markdown", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch history detail for ID {history_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report detail: {str(e)}")

@router.delete("/history/{history_id}")
async def delete_history_item(history_id: int):
    """
    Deletes a specific historical report by ID.
    """
    try:
        success = delete_analysis_report(history_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to delete report with ID {history_id}.")
        return {"status": "deleted", "id": history_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete history item ID {history_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")
