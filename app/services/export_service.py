from sqlalchemy import select
from sqlalchemy import func
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy.ext.asyncio import AsyncSession

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
        comparative = await self._build_comparative_context(db, session_id)
            
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, f"InsightFlow Executive Report: {session.title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        
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
        pdf.multi_cell(0, 10, analysis["summary"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(4)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Leitura Gerencial", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", size=12)
        pdf.multi_cell(
            0,
            10,
            (
                f"Sessoes ativas comparadas: {comparative['active_sessions']} | "
                f"Score medio da instancia: {comparative['portfolio_average_score']} | "
                f"Taxa media de conclusao: {comparative['portfolio_completion_rate']}."
            ),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.multi_cell(
            0,
            10,
            (
                f"Posicao desta sessao no volume: {comparative['response_rank_label']}. "
                f"Posicao em score medio: {comparative['score_rank_label']}."
            ),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Principais Temas Mencionados", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", size=12)
        themes = ", ".join(analysis["top_positive_themes"])
        pdf.multi_cell(
            0,
            10,
            f"Temas Frequentes: {themes if themes else 'Nenhum'}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        
        self.export_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.export_dir / f"session_{session_id}_report_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.pdf"
        pdf.output(str(filepath))
        self._cleanup_old_reports(session_id)
        return str(filepath)

    async def _build_comparative_context(self, db: AsyncSession, session_id: int) -> dict:
        active_sessions = await db.scalar(select(func.count(Session.id)).where(Session.status == "active")) or 0
        portfolio_average_score = await db.scalar(
            select(func.avg(Response.score)).where(Response.score.is_not(None))
        )
        total_responses = await db.scalar(select(func.count(Response.id))) or 0
        completed_responses = await db.scalar(
            select(func.count(Response.id)).where(Response.status == "completed")
        ) or 0
        portfolio_completion_rate = (
            f"{(completed_responses / total_responses * 100):.0f}%"
            if total_responses
            else "-"
        )

        response_counts_stmt = (
            select(Response.session_id, func.count(Response.id).label("response_count"), func.avg(Response.score).label("avg_score"))
            .group_by(Response.session_id)
        )
        response_rows = await db.execute(response_counts_stmt)
        rows = list(response_rows.all())

        sorted_by_volume = sorted(rows, key=lambda item: item.response_count or 0, reverse=True)
        sorted_by_score = sorted(
            [item for item in rows if item.avg_score is not None],
            key=lambda item: float(item.avg_score),
            reverse=True,
        )

        response_rank = next((index + 1 for index, item in enumerate(sorted_by_volume) if item.session_id == session_id), None)
        score_rank = next((index + 1 for index, item in enumerate(sorted_by_score) if item.session_id == session_id), None)

        return {
            "active_sessions": active_sessions,
            "portfolio_average_score": f"{float(portfolio_average_score):.1f}" if portfolio_average_score is not None else "-",
            "portfolio_completion_rate": portfolio_completion_rate,
            "response_rank_label": f"{response_rank}o lugar" if response_rank else "sem ranking",
            "score_rank_label": f"{score_rank}o lugar" if score_rank else "sem ranking",
        }

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
