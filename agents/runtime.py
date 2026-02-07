"""
Agent runtime service - hosts LLM inference.
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import logging

from .model_loader import ModelLoader
from .agent_prompts import get_system_prompt
from .logger import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Coding Buddy Agent Runtime")

# Global model loader
model_loader = None


class GenerateRequest(BaseModel):
    """Request for text generation"""
    agent_type: str
    prompt: str
    max_tokens: int = 2048
    temperature: float = 0.7
    stop: Optional[list] = None


class GenerateResponse(BaseModel):
    """Response from text generation"""
    text: str
    metadata: Dict


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    global model_loader
    
    model_path = os.getenv('MODELS_PATH', '/models') + '/base-model.gguf'
    logger.info(f"Loading model from {model_path}")
    
    model_loader = ModelLoader(model_path)
    logger.info("Model loaded successfully")


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate text using specified agent type.
    """
    logger.info("Received generation request for agent: %s", request.agent_type)
    if model_loader is None:
        logger.error("Model not loaded")
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Get system prompt for agent type
        system_prompt = get_system_prompt(request.agent_type)
        
        # Combine system prompt with user prompt
        full_prompt = f"{system_prompt}\n\n{request.prompt}"
        
        logger.info("Generating with prompt (first 500 chars): %s", full_prompt[:500])
        logger.debug("Generating with prompt: %s", full_prompt)

        # Generate
        response_text = model_loader.generate(
            prompt=full_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop or []
        )
        
        logger.info("Generated response (first 500 chars): %s", response_text[:500])
        logger.debug("Generated response: %s", response_text)

        return GenerateResponse(
            text=response_text,
            metadata={
                'agent_type': request.agent_type,
                'prompt_length': len(full_prompt),
                'response_length': len(response_text)
            }
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'model_loaded': model_loader is not None
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
