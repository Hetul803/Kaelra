"""Voice routes — ElevenLabs TTS when configured, else browser Web Speech fallback."""

import base64

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from config import elevenlabs_configured, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
from auth import get_current_user

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None


@router.get("/voice/status")
async def voice_status(user: dict = Depends(get_current_user)):
    return {
        "provider": "elevenlabs" if elevenlabs_configured() else "browser",
        "configured": elevenlabs_configured(),
        "voice_id": ELEVENLABS_VOICE_ID,
    }


@router.post("/voice/tts")
async def tts(req: TTSRequest, user: dict = Depends(get_current_user)):
    if not elevenlabs_configured():
        # Frontend will fall back to browser speechSynthesis.
        return {"audio": None, "provider": "browser"}
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        stream = client.text_to_speech.convert(
            text=req.text[:2500],
            voice_id=req.voice_id or ELEVENLABS_VOICE_ID,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        data = b"".join(chunk for chunk in stream)
        b64 = base64.b64encode(data).decode()
        return {"audio": f"data:audio/mpeg;base64,{b64}", "provider": "elevenlabs"}
    except Exception as e:  # noqa: BLE001
        return {"audio": None, "provider": "browser", "error": str(e)}
