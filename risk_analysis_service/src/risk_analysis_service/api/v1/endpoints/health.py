from fastapi import APIRouter


router = APIRouter(tags=["Health Check"])


@router.get("/")
async def root():
    """Перевірка стану сервісу."""
    return {"status": "ok", "service": "Risk Analysis Service"}
