import os
import asyncio

import pytest

sd = pytest.importorskip("sounddevice")

from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================
# Load API key
# =========================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    pytest.skip(
        "GEMINI_API_KEY not found in .env",
        allow_module_level=True,
    )


# =========================
# Gemini
# =========================

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.1-flash-live-preview"


# =========================
# Audio settings
# =========================

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1600       # ~100 ms

MIC_DEVICE = 1
SPEAKER_DEVICE = 3


# =========================
# Microphone → Gemini
# =========================

async def send_microphone(session):

    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()

    def microphone_callback(indata, frames, time, status):

        if status:
            print("Microphone:", status)

        audio_bytes = indata.copy().tobytes()

        loop.call_soon_threadsafe(
            audio_queue.put_nowait,
            audio_bytes
        )

    print("🎤 Microphone started")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=BLOCK_SIZE,
        device=MIC_DEVICE,
        callback=microphone_callback
    ):

        while True:

            audio_bytes = await audio_queue.get()

            await session.send_realtime_input(
                audio=types.Blob(
                    data=audio_bytes,
                    mime_type="audio/pcm;rate=16000"
                )
            )


# =========================
# Gemini → Speaker
# =========================

async def receive_response(session):

    print("🔊 Speaker started")

    speaker = sd.RawOutputStream(
        samplerate=24000,
        channels=1,
        dtype="int16",
        device=SPEAKER_DEVICE
    )

    speaker.start()

    try:

        async for response in session.receive():

            if not response.server_content:
                continue

            content = response.server_content

            # Customer speech transcription
            if content.input_transcription:

                print(
                    "\nCustomer:",
                    content.input_transcription.text
                )

            # Gemini response transcription
            if content.output_transcription:

                print(
                    "\nAssistant:",
                    content.output_transcription.text
                )

            # Gemini audio
            if content.model_turn:

                for part in content.model_turn.parts:

                    if part.inline_data:

                        audio_data = part.inline_data.data

                        speaker.write(audio_data)

            if content.turn_complete:

                print("\n--- Turn complete ---")

    finally:

        speaker.stop()
        speaker.close()


# =========================
# Main
# =========================

async def main():

    config = {

        "response_modalities": ["AUDIO"],

        "input_audio_transcription": {},

        "output_audio_transcription": {},

        "system_instruction": """
You are a multilingual telecom customer-care assistant.

Supported languages:

English
Tamil
Hindi
Telugu
Kannada
Malayalam

Rules:

1. Respond in the customer's language whenever possible.
2. Do not intentionally switch to unsupported languages.
3. Be concise and professional.
4. Help customers with telecom-related problems.
5. Ask clarifying questions when necessary.
"""
    }

    print("Connecting to Gemini Live...")

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        print()
        print("========================================")
        print("   MULTILINGUAL GENAI VOICE ASSISTANT")
        print("========================================")
        print("✅ Gemini Live connected")
        print("🎤 Microphone: Device 1")
        print("🔊 Speaker: Device 3")
        print("🗣️ Speak normally")
        print("⛔ Press Ctrl+C to stop")
        print("========================================")
        print()

        await asyncio.gather(
            send_microphone(session),
            receive_response(session)
        )


# =========================
# Run
# =========================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\n\nVoice assistant stopped.")
