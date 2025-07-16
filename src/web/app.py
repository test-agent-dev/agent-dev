"""FastAPI application for TESTIA."""
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.llm_connector.factory import ModelFactory

app = FastAPI(title="TESTIA API")
logger = logging.getLogger(__name__)

model_factory: Optional[ModelFactory] = None


class ChatRequest(BaseModel):
    message: str
    model: str
    conversation_id: Optional[str] = None


@app.on_event("startup")
async def startup() -> None:
    global model_factory
    model_factory = ModelFactory()
    logger.info("Model factory loaded")


@app.post("/api/chat")
async def chat_endpoint(data: ChatRequest):
    """Generate a response using the requested model."""
    if model_factory is None:
        raise HTTPException(status_code=503, detail="Model factory not ready")
    try:
        provider = await model_factory.get_client(data.model)
        messages = [{"role": "user", "content": data.message}]
        response = await provider.generate_response(messages)
        return {"response": response, "model": data.model}
    except Exception as exc:
        logger.error("Chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/models-config")
async def models_config():
    if model_factory is None:
        raise HTTPException(status_code=503, detail="Model factory not ready")
    return {"models": list(model_factory.configs.keys())}


def run_web_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)
