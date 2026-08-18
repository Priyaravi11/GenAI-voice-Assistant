import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# Gemini Client
# ============================================================

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


# ============================================================
# Model
# ============================================================

GEMINI_LIVE_MODEL = os.getenv(
    "GEMINI_LIVE_MODEL",
    "gemini-3.1-flash-live-preview",
)

GEMINI_TEXT_MODELS = [
    model.strip()
    for model in os.getenv(
        "GEMINI_TEXT_MODELS",
        "gemini-2.5-flash,gemini-2.0-flash",
    ).split(",")
    if model.strip()
]


def _is_quota_error(error: Exception) -> bool:
    err_str = str(error)
    return (
        "429" in err_str
        or "RESOURCE_EXHAUSTED" in err_str
        or "quota" in err_str.lower()
    )


def _is_retryable_error(error: Exception) -> bool:
    err_str = str(error)
    return "503" in err_str or "UNAVAILABLE" in err_str


# ============================================================
# Supported Languages
# ============================================================

SUPPORTED_LANGUAGES = [
    "English",
    "Tamil",
    "Hindi",
    "Telugu",
    "Kannada",
    "Malayalam",
]


# ============================================================
# System Instruction
# ============================================================

SYSTEM_INSTRUCTION = """
You are a multilingual telecom customer-care voice assistant.

Your job is to help customers with telecom-related problems.

Supported languages:
- English
- Tamil
- Hindi
- Telugu
- Kannada
- Malayalam

Rules:

1. Identify the language used by the customer.
2. Respond in the same language whenever possible.
3. Do not intentionally switch to another language.
4. Keep responses concise and professional.
5. Ask a clarification question when required.
6. Do not invent customer account information.
7. Do not invent billing, payment, subscription,
   network or account details.
8. If information is unavailable, say that you
   need to check the customer's account or system.
9. If the issue requires human intervention,
   indicate that the customer can be escalated
   to a human agent.
"""


# ============================================================
# Create Live API Configuration
# ============================================================

def get_live_config():
    """
    Returns configuration used when creating
    a Gemini Live session.
    """

    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],

        input_audio_transcription=types.AudioTranscriptionConfig(),

        output_audio_transcription=types.AudioTranscriptionConfig(),

        system_instruction=types.Content(
            parts=[
                types.Part(
                    text=SYSTEM_INSTRUCTION
                )
            ]
        ),
    )


# ============================================================
# Create Gemini Live Session
# ============================================================

async def create_live_session():
    """
    Creates and returns a Gemini Live session context manager.

    Usage:

        async with await create_live_session() as session:
            ...

    The caller is responsible for entering and keeping the session
    context alive.
    """

    return client.aio.live.connect(
        model=GEMINI_LIVE_MODEL,
        config=get_live_config(),
    )


# ============================================================
# Text-only Gemini Test
# ============================================================

async def generate_text(prompt: str) -> str:
    """
    Simple text-generation helper.

    Useful for:
    - testing Gemini
    - fallback responses
    - RAG response generation
    - debugging
    
    Args:
        prompt: The prompt text to send to Gemini
        
    Returns:
        The generated response text
        
    Raises:
        ValueError: If prompt is empty
        Exception: If Gemini API call fails
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    if len(prompt) > 100000:
        raise ValueError("Prompt exceeds maximum length (100k chars)")

    models_to_try = GEMINI_TEXT_MODELS

    last_exception = None
    quota_exhausted = False

    if client is not None:
        for model_name in models_to_try:
            for attempt in range(3):
                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )

                    if response and response.text:
                        return response.text

                except Exception as e:
                    last_exception = e
                    if _is_quota_error(e):
                        logger.warning(
                            f"Gemini quota exhausted for model {model_name}; "
                            "switching to fallback provider."
                        )
                        quota_exhausted = True
                        break

                    if _is_retryable_error(e):
                        import asyncio
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue

                    # For non-retryable errors, switch model immediately
                    break

            if quota_exhausted:
                break
    else:
        last_exception = RuntimeError(
            "GEMINI_API_KEY not found in environment variables"
        )
        logger.warning("Gemini client is not configured; using fallback provider.")

    # Attempt Mantle fallback if Gemini models fail
    try:
        from backend.app.ollama_provider import ollama_provider
        fallback_response = await ollama_provider.generate_text(prompt)
        if fallback_response:
            return fallback_response
    except Exception as fallback_err:
        logger.warning(f"Mantle fallback attempt failed: {str(fallback_err)}")

    raise RuntimeError(f"Gemini generation failed across models: {str(last_exception)}")


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """
    Transcribe a recorded audio clip using the regular Gemini model API.
    This is used by the demo recording flow instead of Gemini Live.
    """

    if not audio_bytes:
        raise ValueError("Audio cannot be empty")

    if client is None:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")

    prompt = (
        "Transcribe this customer support audio. Return only the spoken text. "
        "Do not add labels, timestamps, markdown, or commentary."
    )

    last_exception = None

    for model_name in GEMINI_TEXT_MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=mime_type,
                    ),
                ],
            )

            transcript = (response.text or "").strip() if response else ""
            if transcript:
                return transcript

        except Exception as e:
            last_exception = e
            if _is_quota_error(e):
                logger.warning(
                    f"Gemini transcription quota exhausted for model {model_name}."
                )
                break

            if _is_retryable_error(e):
                import asyncio
                await asyncio.sleep(1.0)
                continue

    raise RuntimeError(f"Audio transcription failed: {str(last_exception)}")


# ============================================================
# Streaming Text Generation
# ============================================================

async def generate_text_streaming(prompt: str):
    """
    Stream response text from Gemini for real-time output.

    Useful for:
    - Real-time transcription feedback
    - Progressive response display
    - Lower latency perception
    
    Args:
        prompt: The prompt text
        
    Yields:
        Text chunks as they are generated
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    if client is None:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")

    try:
        async with await client.aio.models.generate_content_stream(
            model=GEMINI_TEXT_MODELS[0],
            contents=prompt,
        ) as stream:
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text

    except Exception as e:
        raise RuntimeError(f"Gemini streaming failed: {str(e)}")


# ============================================================
# Gemini Health Check
# ============================================================

async def health_check() -> dict:
    """
    Checks whether Gemini API is reachable.
    """

    try:

        response = await generate_text(
            "Reply with exactly: Gemini connection OK"
        )

        return {
            "status": "ok",
            "response": response,
        }

    except Exception as exc:

        return {
            "status": "error",
            "error": str(exc),
        }
