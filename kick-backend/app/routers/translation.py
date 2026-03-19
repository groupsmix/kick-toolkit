"""Multi-Language Chat Translation router."""

import logging

from fastapi import APIRouter, Depends

from app.dependencies import require_auth
from app.models.schemas import TranslationSettingsUpdate, TranslationRequest, TranslationResult
from app.repositories import translation as trans_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/translation", tags=["translation"])


@router.get("/settings/{channel}")
async def get_settings(channel: str, _session: dict = Depends(require_auth)) -> dict:
    settings = await trans_repo.get_settings(channel)
    if settings:
        return settings
    return {"channel": channel, "enabled": False, "target_language": "en", "auto_translate": False}


@router.post("/settings/{channel}")
async def update_settings(
    channel: str, body: TranslationSettingsUpdate, _session: dict = Depends(require_auth)
) -> dict:
    result = await trans_repo.upsert_settings(
        channel=channel, enabled=body.enabled,
        target_language=body.target_language, auto_translate=body.auto_translate,
    )
    logger.info("Translation settings updated for channel=%s", channel)
    return result


@router.post("/translate")
async def translate_text(
    body: TranslationRequest, _session: dict = Depends(require_auth)
) -> dict:
    # Placeholder translation — in production, integrate with a translation API
    return {
        "original_text": body.text,
        "translated_text": body.text,  # passthrough until API integration
        "source_language": body.source_language or "auto",
        "target_language": body.target_language,
    }
