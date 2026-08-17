import os
import asyncio
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.1-flash-live-preview"

async def main():

    config = {
        "response_modalities": ["AUDIO"],

        "input_audio_transcription": {},
        "output_audio_transcription": {},

        "system_instruction": """
You are a multilingual telecom customer-care assistant.

Supported languages:
- English
- Tamil
- Hindi
- Telugu
- Kannada
- Malayalam

Rules:
1. Respond in the customer's language whenever possible.
2. Do not intentionally switch to unsupported languages.
3. Be concise and professional.
4. Help customers with telecom-related problems.
"""
    }

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        print("Gemini Live connected!")

        await session.send_realtime_input(
            text="Hello, I have an internet problem."
        )

        async for response in session.receive():

            if response.server_content:

                if response.server_content.input_transcription:
                    print(
                        "Customer:",
                        response.server_content.input_transcription.text
                    )

                if response.server_content.output_transcription:
                    print(
                        "Assistant:",
                        response.server_content.output_transcription.text
                    )

                if response.server_content.turn_complete:
                    print("Turn complete.")
                    break


if __name__ == "__main__":
    asyncio.run(main())