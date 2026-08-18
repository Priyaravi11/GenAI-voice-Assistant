import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


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

GEMINI_LIVE_MODEL = "gemini-3.1-flash-live-preview"


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
    Creates and returns a Gemini Live session.

    Usage:

        session = await create_live_session()

    The caller is responsible for keeping the
    session context alive.
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

    if client is None:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")

    if len(prompt) > 100000:
        raise ValueError("Prompt exceeds maximum length (100k chars)")

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    last_exception = None

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
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                    import asyncio
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                # For non-retryable errors, switch model immediately
                break

    # Attempt Ollama Fallback if Gemini models fail
    try:
        from backend.app.ollama_provider import ollama_provider
        ollama_response = await ollama_provider.generate_text(prompt)
        if ollama_response:
            return ollama_response
    except Exception as ollama_err:
        logger.warning(f"Ollama fallback attempt failed: {str(ollama_err)}")

    raise RuntimeError(f"Gemini generation failed across models: {str(last_exception)}")


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
            model="gemini-3.6-flash",
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
