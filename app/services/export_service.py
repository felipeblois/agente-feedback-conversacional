from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.response import Response
from app.models.message import Message
from app.models.session import Session
from app.services.analysis_service import analysis_service

class ExportService:
    def __init__(self) -> None:
        self.export_dir = Path("data/exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.keep_reports_per_session = 2

    async def generate_csv(self, db: AsyncSession, session_id: int) -> Optional[str]:
        stmt = select(Message, Response.score).join(Response).where(Response.session_id == session_id, Message.sender == "participant")
        result = await db.execute(stmt)
        rows = result.all()
        
        if not rows:
            return None
            
        data = []
        for msg, score in rows:
            data.append({
                "response_id": msg.response_id,
                "score": score,
                "message_order": msg.message_order,
                "text": msg.message_text,
                "timestamp": msg.created_at.isoformat()
            })
            
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
        
    async def generate_pdf(self, db: AsyncSession, session_id: int) -> Optional[str]:
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            return None
            
        analysis = await analysis_service.get_latest(db, session_id)
        if not analysis:
            return None
            
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, f"Feedback Report: {session.title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
        pdf.set_font("helvetica", size=12)
        pdf.ln(10)
        
        avg = analysis["avg_score"] if analysis["avg_score"] else 0
        pdf.cell(
            0,
            10,
            f"Score Medio: {avg:.2f} | Total de Respostas: {analysis['response_count']}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Resumo Executivo", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", size=12)
        pdf.multi_cell(0, 10, analysis["summary"])
        
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Principais Temas Mencionados", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", size=12)
        themes = ", ".join(analysis["top_positive_themes"])
        pdf.multi_cell(0, 10, f"Temas Frequentes: {themes if themes else 'Nenhum'}")
        
        self.export_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.export_dir / f"session_{session_id}_report_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.pdf"
        pdf.output(str(filepath))
        self._cleanup_old_reports(session_id)
        return str(filepath)

    def delete_session_exports(self, session_id: int) -> int:
        removed = 0
        for file_path in self._session_report_files(session_id):
            try:
                file_path.unlink()
                removed += 1
            except FileNotFoundError:
                continue
        return removed

    def _cleanup_old_reports(self, session_id: int) -> None:
        report_files = self._session_report_files(session_id)
        for file_path in report_files[self.keep_reports_per_session:]:
            try:
                file_path.unlink()
            except FileNotFoundError:
                continue

    def _session_report_files(self, session_id: int) -> List[Path]:
        pattern = f"session_{session_id}_report_*.pdf"
        return sorted(
            self.export_dir.glob(pattern),
            key=lambda item: item.name,
            reverse=True,
        )

export_service = ExportService()
