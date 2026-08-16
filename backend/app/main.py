from fastapi import FastAPI

from backend.app.api.routes import analytics
from backend.app.api.routes import calls
from backend.app.api.routes import rag
from backend.app.api.routes import session
from backend.app.api.routes import tools

from backend.app.websocket import router as websocket_router


app = FastAPI(
    title="Multilingual GenAI Voice Assistant",
    description="Telecom customer-care backend",
    version="1.0.0",
)


app.include_router(session.router)
app.include_router(calls.router)
app.include_router(analytics.router)
app.include_router(rag.router)
app.include_router(tools.router)

app.include_router(websocket_router)


@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Multilingual GenAI Voice Assistant API is running"
    }