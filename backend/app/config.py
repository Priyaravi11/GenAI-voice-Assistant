import os
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv()


class Settings:
    # Application
    APP_NAME = os.getenv(
        "APP_NAME",
        "Multilingual GenAI Voice Assistant"
    )

    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_LIVE_MODEL = os.getenv(
        "GEMINI_LIVE_MODEL",
        "gemini-3.1-flash-live-preview",
    )
    GEMINI_TEXT_MODELS = os.getenv(
        "GEMINI_TEXT_MODELS",
        "gemini-2.5-flash,gemini-2.0-flash",
    )

    # Mantle / Cloud LLM fallback
    MANTLE_API_KEY = os.getenv("MANTLE_API_KEY") or os.getenv(
        "AWS_BEARER_TOKEN_BEDROCK"
    )
    MANTLE_API_KEY_B64 = os.getenv("MANTLE_API_KEY_B64") or os.getenv(
        "AWS_BEARER_TOKEN_BEDROCK_B64"
    )
    MANTLE_HOST = os.getenv(
        "MANTLE_HOST",
        "https://bedrock-mantle.us-east-1.api.aws/v1",
    )
    MANTLE_MODEL = os.getenv("MANTLE_MODEL", "openai.gpt-oss-20b")

    # Legacy Ollama settings. Kept for backward compatibility.
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://api.ollama.com")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

    # RAG / ChromaDB
    CHROMA_PATH = os.getenv("CHROMA_PATH", "rag/data/chroma")
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "telecom_knowledge")

    # Frontend / CORS
    FRONTEND_URL = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    )


settings = Settings()
