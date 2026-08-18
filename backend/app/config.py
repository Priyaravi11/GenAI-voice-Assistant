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

    # Ollama / Cloud / Local LLM
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://api.ollama.com")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

    # Frontend / CORS
    FRONTEND_URL = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    )


settings = Settings()