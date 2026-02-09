import logging
import sys
from rich.logging import RichHandler
import json
import threading
import datetime

_thread_local = threading.local()

class WorkflowIDFilter(logging.Filter):
    def filter(self, record):
        record.workflow_id = getattr(_thread_local, 'workflow_id', None)
        return True

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "workflow_id": record.workflow_id,
            "name": record.name,
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def set_workflow_id(workflow_id: str):
    _thread_local.workflow_id = workflow_id

def clear_workflow_id():
    if hasattr(_thread_local, 'workflow_id'):
        del _thread_local.workflow_id

def setup_logging(log_level="INFO"):
    """
    Set up logging to console and file, with support for rich markup.
    """
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Console Handler (RichHandler)
    console_handler = RichHandler(rich_tracebacks=True, markup=True)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    console_handler.addFilter(WorkflowIDFilter())
    logging.root.addHandler(console_handler)

    # File Handler (JSON)
    file_handler = logging.FileHandler("/tmp/orchestrator.log")
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(WorkflowIDFilter())
    logging.root.addHandler(file_handler)

    logging.root.setLevel(log_level)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info("Logging initialized")
