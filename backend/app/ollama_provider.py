"""
Ollama LLM Provider Integration
File: backend/app/ollama_provider.py

Provides seamless integration with Ollama (Local and Remote Cloud/API instances).
Offers text generation fallback for agents when Gemini or secondary providers are unavailable.
"""

import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.logger import get_logger

logger = get_logger(__name__)

class OllamaProvider:
    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        self.host = (host or settings.OLLAMA_HOST or "http://localhost:11434").rstrip("/")
        self.api_key = api_key or settings.OLLAMA_API_KEY
        self.default_model = settings.OLLAMA_MODEL or "llama3.2"

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def list_available_models(self) -> List[str]:
        """Fetch list of pulled/available free models from Ollama endpoint."""
        url = f"{self.host}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    logger.info(f"Ollama models found: {models}")
                    return models
                else:
                    logger.warning(f"Ollama list tags failed status {response.status_code}: {response.text}")
                    return []
        except Exception as e:
            logger.warning(f"Unable to connect to Ollama host at {self.host}: {str(e)}")
            return []

    async def generate_text(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Generate text using cloud model via API key."""
        target_model = model or self.default_model

        # Try native Ollama endpoint first
        url = f"{self.host}/api/generate"
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self._get_headers())
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                
                # Try OpenAI-compatible chat endpoint fallback for cloud gateways
                chat_url = f"{self.host}/v1/chat/completions"
                chat_payload = {
                    "model": target_model,
                    "messages": [{"role": "user", "content": prompt}]
                }
                chat_resp = await client.post(chat_url, json=chat_payload, headers=self._get_headers())
                if chat_resp.status_code == 200:
                    res_json = chat_resp.json()
                    return res_json.get("choices", [{}])[0].get("message", {}).get("content", "")

                logger.error(f"Cloud generation failed ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            logger.error(f"Cloud generation error: {str(e)}")
            return None

ollama_provider = OllamaProvider()
