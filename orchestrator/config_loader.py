"""
Configuration and logging utilities.
"""
import yaml
import logging
from pathlib import Path
from typing import Dict


class ConfigLoader:
    """Load system configuration"""
    
    DEFAULT_CONFIG = {
        'max_retries': 3,
        'enable_refining': False,
        'coverage_threshold': 80.0,
        'agent_timeout': 300,
        'test_timeout': 300,
        'model_path': '/models/base-model.gguf',
        'context_size': 4096,
        'max_tokens': 2048,
        'temperature': 0.7
    }
    
    @classmethod
    def load(cls, config_path: str = '/app/config/config.yaml') -> Dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Merge with defaults
            full_config = cls.DEFAULT_CONFIG.copy()
            full_config.update(config)
            
            return full_config
            
        except FileNotFoundError:
            logging.warning(f"Config file not found: {config_path}, using defaults")
            return cls.DEFAULT_CONFIG


def setup_logging(level: str = 'INFO'):
    """Configure logging"""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/state/orchestrator.log')
        ]
    )
