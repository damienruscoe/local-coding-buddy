"""
Manages the history of requests made to agents.
"""
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def write_file(file_path, contents):
    with open(file_path, 'w') as f:
        f.write(contents)

class RequestHistory:
    """
    Manages the history of requests made to agents.
    """
    def __init__(self, base_dir: str = '/workspace/request_history'):
        self.base_dir = Path(base_dir)
        self.workflow_dir = None
        self.call_index = 0
        self._setup_workflow_dir()

    def _setup_workflow_dir(self):
        try:
            self.workflow_dir = self.base_dir / str(int(time.time()))
            self.workflow_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created request history directory for current workflow: {self.workflow_dir}")
        except OSError as e:
            logger.error(f"Failed to create request history directory: {e}")

    def _check(self, direction: str):
        if not self.workflow_dir:
            logger.error(f"Request history directory not available. Skipping saving {direction}.")
            return False
        return True

    def _save(self, agent_name: str, direction: str, prompt: str):
        if not self._check(direction):
            return

        file_name = f"{self.call_index:03d}_{agent_name}_{direction}.txt"
        file_path = self.workflow_dir / file_name
        try:
            write_file(file_path, prompt)
            logger.info(f"Saved request to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save {direction} to file: {e}")

    def save_request(self, agent_name: str, prompt: str):
        self.call_index += 1
        self._save(agent_name, 'request', prompt)

    def save_response(self, agent_name: str, prompt: str):
        self._save(agent_name, 'response', prompt)

    def read_request(self, file_path: str) -> str:
        """
        Reads a request from a file.
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            logger.info(f"Read request from {file_path}")
            return content
        except IOError as e:
            logger.error(f"Failed to read request from file: {e}")
            raise
