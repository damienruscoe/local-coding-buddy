import logging
import sys
from rich.logging import RichHandler

def setup_logging(log_level="INFO"):
    """
    Set up logging to console and file, with support for rich markup.
    """
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True),
            logging.FileHandler("/tmp/agent.log"),
        ],
    )

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info("Agent logging initialized")
