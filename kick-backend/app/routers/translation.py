"""Multi-Language Chat Translation router."""

import logging

from fastapi import APIRouter, Depends

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import TranslationRequest, TranslationSettingsUpdate
from app.repositories import translation as translation_repo
from app.services.translation import translate_text, SUPPORTED_LANGUAGES, detect_language

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/translation", tags=["translation"])


@router.post("/translate")
async def translate(
    body: TranslationRequest, _session: dict = Depends(require_auth)
) -> dict:
    result = await translate_text(body.text, body.target_language, body.source_language)
    return result


@router.get("/languages")
async def list_languages(_session: dict = Depends(require_auth)) -> list[dict]:
    return SUPPORTED_LANGUAGES


@router.get("/detect")
async def detect(text: str, _session: dict = Depends(require_auth)) -> dict:
    lang = detect_language(text)
    return {"text": text, "detected_language": lang}


@router.get("/settings/{channel}")
async def get_settings(
    channel: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    settings = await translation_repo.get_settings(channel)
    if settings:
        return settings
    return {
        "channel": channel, "enabled": False,
        "target_language": "en", "auto_translate": False,
        "show_original": True,
    }


@router.post("/settings/{channel}")
async def update_settings(
    channel: str, body: TranslationSettingsUpdate,
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    result = await translation_repo.upsert_settings(
        channel, body.enabled, body.target_language,
        body.auto_translate, body.show_original,
    )
    logger.info("Translation settings updated for channel=%s", channel)
    return result
