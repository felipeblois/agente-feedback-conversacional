from fastapi import APIRouter

from app.core.observability import observability_service
from app.core.security import require_admin_api_key
from fastapi import Depends

router = APIRouter()

@router.get("")
async def health_check():
    return {"status": "ok"}


@router.get("/operational")
async def operational_health(_: str = Depends(require_admin_api_key)):
    snapshot = observability_service.snapshot()
    return snapshot
