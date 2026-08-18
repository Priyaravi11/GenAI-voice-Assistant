"""
Mantle LLM Provider Integration
File: backend/app/ollama_provider.py

Provides a Bedrock Mantle text-generation fallback for agents when Gemini
is unavailable. The module keeps the historical ollama_provider symbol so
existing imports continue to work.
"""

import httpx
import binascii
import base64
import re
from typing import List, Dict, Optional
from backend.app.config import settings
from backend.app.logger import get_logger

logger = get_logger(__name__)


def _decode_base64_secret(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    try:
        decoded = base64.b64decode(value.strip(), validate=True)
        text = decoded.lstrip(b"\x00").decode("utf-8", errors="ignore").strip()
        match = re.search(r"(MantleApiKey-[A-Za-z0-9:_=+./-]+)", text)
        return match.group(1) if match else text or None
    except (binascii.Error, UnicodeDecodeError):
        return None


def _resolve_api_key(raw_key: Optional[str], encoded_key: Optional[str]) -> Optional[str]:
    if raw_key and raw_key.strip():
        key = raw_key.strip()
        return _decode_base64_secret(key) or key

    return _decode_base64_secret(encoded_key)


class MantleProvider:
    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        self.host = (
            host
            or settings.MANTLE_HOST
            or "https://bedrock-mantle.us-east-1.api.aws/v1"
        ).rstrip("/")
        self.api_key = (
            api_key
            or _resolve_api_key(
                settings.MANTLE_API_KEY,
                settings.MANTLE_API_KEY_B64,
            )
        )
        self.default_model = settings.MANTLE_MODEL or "openai.gpt-oss-20b"

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def list_available_models(self) -> List[str]:
        """Fetch available models from the Bedrock Mantle endpoint."""
        url = f"{self.host}/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    data = response.json()
                    models = [
                        m.get("id")
                        for m in data.get("data", [])
                        if m.get("id")
                    ]
                    logger.info(f"Mantle models found: {models}")
                    return models
                else:
                    logger.warning(
                        f"Mantle model list failed status "
                        f"{response.status_code}: {response.text}"
                    )
                    return []
        except Exception as e:
            logger.warning(
                f"Unable to connect to Mantle host at {self.host}: {str(e)}"
            )
            return []

    async def generate_text(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Generate text through Bedrock Mantle Chat Completions."""
        target_model = model or self.default_model

        if not self.api_key:
            logger.error("Mantle API key is not configured")
            return None

        url = f"{self.host}/chat/completions"
        payload = {
            "model": target_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise multilingual telecom "
                        "customer-care assistant."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self._get_headers())
                if response.status_code == 200:
                    result = response.json()
                    return (
                        result.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

                logger.error(
                    f"Mantle generation failed ({response.status_code}): "
                    f"{response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Mantle generation error: {str(e)}")
            return None

mantle_provider = MantleProvider()
ollama_provider = mantle_provider
