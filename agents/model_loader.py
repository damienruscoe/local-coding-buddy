"""
Model loader using llama.cpp.
"""
import logging
from llama_cpp import Llama

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Loads and manages GGUF models via llama.cpp.
    """
    
    def __init__(self, model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
        """
        Initialize model.
        
        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU (0 for CPU only)
        """
        logger.info(f"Loading model: {model_path}")
        
        self.model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )
        
        logger.info("Model loaded successfully")
    
    def generate(self, prompt: str, max_tokens: int = 2048, 
                 temperature: float = 0.7, stop: list = None) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences
            
        Returns:
            Generated text
        """
        if stop is None:
            stop = []
        
        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
            echo=False
        )
        
        return output['choices'][0]['text']
