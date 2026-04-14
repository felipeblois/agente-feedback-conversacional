from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Deque, Dict, Optional, Tuple

from fastapi import HTTPException

from app.core.observability import log_event
from app.models.session import Session


class PublicAccessService:
    def __init__(self) -> None:
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._limits = {
            "page": (60, 60),
            "start": (12, 300),
            "score": (40, 60),
            "message": (40, 60),
            "finish": (20, 60),
        }

    def validate_session_access(
        self,
        session: Optional[Session],
        public_token: str,
        route_name: str,
        client_ip: str,
        user_agent: str,
    ) -> Session:
        if not session or session.status != "active":
            log_event(
                "warning",
                "public_access_denied",
                reason="invalid_or_inactive",
                public_token=public_token,
                route=route_name,
                client=client_ip,
            )
            raise HTTPException(status_code=404, detail="Link publico indisponivel.")

        if not session.public_link_enabled:
            log_event(
                "warning",
                "public_access_denied",
                reason="link_disabled",
                session_id=session.id,
                route=route_name,
                client=client_ip,
            )
            raise HTTPException(status_code=410, detail="Link publico indisponivel.")

        if session.public_link_revoked_at:
            log_event(
                "warning",
                "public_access_denied",
                reason="link_revoked",
                session_id=session.id,
                route=route_name,
                client=client_ip,
            )
            raise HTTPException(status_code=410, detail="Link publico indisponivel.")

        if session.public_link_expires_at and session.public_link_expires_at <= self._utcnow_naive():
            log_event(
                "warning",
                "public_access_denied",
                reason="link_expired",
                session_id=session.id,
                route=route_name,
                client=client_ip,
            )
            raise HTTPException(status_code=410, detail="Link publico indisponivel.")

        self._apply_rate_limit(session.id, public_token, route_name, client_ip, user_agent)
        return session

    def check_honeypot(self, session_id: int, public_token: str, client_ip: str, honeypot_value: str) -> None:
        if honeypot_value.strip():
            log_event(
                "warning",
                "public_spam_blocked",
                session_id=session_id,
                public_token=public_token,
                client=client_ip,
                reason="honeypot_triggered",
            )
            raise HTTPException(status_code=400, detail="Nao foi possivel iniciar o feedback.")

    def public_link_status(self, session: Session) -> str:
        if session.public_link_revoked_at:
            return "revoked"
        if not session.public_link_enabled:
            return "disabled"
        if session.public_link_expires_at and session.public_link_expires_at <= self._utcnow_naive():
            return "expired"
        if session.status != "active":
            return "inactive"
        return "active"

    def _apply_rate_limit(
        self,
        session_id: int,
        public_token: str,
        route_name: str,
        client_ip: str,
        user_agent: str,
    ) -> None:
        limit, window_seconds = self._limits.get(route_name, (30, 60))
        key = f"{public_token}:{client_ip}:{route_name}"
        now = self._utcnow_naive().timestamp()
        events = self._events[key]

        while events and now - events[0] > window_seconds:
            events.popleft()

        if len(events) >= limit:
            log_event(
                "warning",
                "public_rate_limit_hit",
                session_id=session_id,
                route=route_name,
                client=client_ip,
                user_agent=user_agent[:120] if user_agent else "unknown",
                limit=limit,
                window_seconds=window_seconds,
            )
            raise HTTPException(
                status_code=429,
                detail="Limite temporario de tentativas atingido. Aguarde um instante e tente novamente.",
            )

        events.append(now)

    def _utcnow_naive(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)


public_access_service = PublicAccessService()
