from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi import WebSocket
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from ....core.config import get_settings
from ....db.session import get_db
from ....db.models.organization import User
from ....core.socket_manager import manager
from ....schemas.security_alert import SecurityAlertOut
from ....db.models.security_alert import SecurityAlert
from sqlalchemy import select


router = APIRouter(tags=["WebSockets"])
logger = logging.getLogger("risk_analysis.ws")
settings = get_settings()


async def _authenticate_ws(websocket: WebSocket, db: Session) -> Optional[User]:
    """Authenticate WebSocket using JWT provided as query parameter 'token'."""
    token = websocket.query_params.get("token")
    if not token:
        logger.info("WS auth failed: missing token query param")
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject: str | None = payload.get("sub")
        if subject is None:
            logger.info("WS auth failed: token missing 'sub' claim")
            return None
        user_id = uuid.UUID(subject)
    except (JWTError, ValueError):
        logger.info("WS auth failed: invalid token or subject UUID parse error")
        return None
    user: Optional[User] = db.get(User, user_id)
    if user is None:
        logger.info("WS auth failed: user not found id=%s", subject)
    return user


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming real-time alerts to authenticated users.

    Expects JWT access token in query parameter: ?token=...
    """
                                                                              
    db: Session = next(get_db())                            
    try:
        user = await _authenticate_ws(websocket, db)
        if user is None or not user.is_active:
                                           
            await websocket.close(code=1008)
            return
        org_id = user.organization_id
        await manager.connect(websocket, org_id)
        logger.info("WebSocket connected for org=%s user=%s", org_id, user.id)

                                                                      
        try:
            limit_raw = websocket.query_params.get("initial_limit")
            limit = int(limit_raw) if limit_raw is not None else 50
            if limit < 1:
                limit = 1
            if limit > 200:
                limit = 200
        except Exception:
            limit = 50
        try:
            stmt = (
                select(SecurityAlert)
                .where(SecurityAlert.organization_id == org_id)
                .order_by(SecurityAlert.created_at.desc())
                .limit(limit)
            )
            initial_alerts = db.execute(stmt).scalars().all()
            payload = [
                SecurityAlertOut.model_validate(a).model_dump(mode="json")
                for a in initial_alerts
            ]
            logger.info(
                "Sending initial snapshot: org=%s count=%d", org_id, len(payload)
            )
            await websocket.send_json({"type": "snapshot", "items": payload})
        except Exception as exc:
            logger.exception("Failed to send initial alerts snapshot: %s", exc)

        try:
                                                                                         
            while True:
                                                                                        
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for org=%s user=%s", org_id, user.id)
        finally:
            manager.disconnect(websocket, org_id)
    finally:
        try:
            db.close()
        except Exception:
            pass
