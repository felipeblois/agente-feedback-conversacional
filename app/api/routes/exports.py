from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse, Response
import os

from app.api.dependencies import get_db_session
from app.services.export_service import export_service

router = APIRouter()

@router.get("/{session_id}/export/csv")
async def export_csv(session_id: int, db: AsyncSession = Depends(get_db_session)):
    csv_data = await export_service.generate_csv(db, session_id)
    if not csv_data:
        raise HTTPException(status_code=404, detail="No data to export")
        
    return Response(
        content=csv_data, 
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=session_{session_id}_responses.csv"}
    )

@router.get("/{session_id}/export/pdf")
async def export_pdf(session_id: int, db: AsyncSession = Depends(get_db_session)):
    file_path = await export_service.generate_pdf(db, session_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Could not generate PDF")
        
    return FileResponse(
        path=file_path, 
        filename=f"session_{session_id}_report.pdf",
        media_type="application/pdf"
    )
