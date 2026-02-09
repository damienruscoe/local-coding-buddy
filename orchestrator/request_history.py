"""
Manages the history of requests made to agents.
"""
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

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
        """
        Creates the base and workflow directories.
        """
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            workflow_name = str(int(time.time()))
            self.workflow_dir = self.base_dir / workflow_name
            self.workflow_dir.mkdir()
            logger.info(f"Created request history directory for current workflow: {self.workflow_dir}")
        except OSError as e:
            logger.error(f"Failed to create request history directory: {e}")
            self.workflow_dir = None

    def save_request(self, agent_name: str, prompt: str):
        """
        Saves a request to a file.
        """
        if not self.workflow_dir:
            logger.error("Request history directory not available. Skipping saving request.")
            return

        self.call_index += 1
        file_name = f"{self.call_index:03d}_{agent_name}_request.txt"
        try:
            file_path = self.workflow_dir / file_name
            with open(file_path, 'w') as f:
                f.write(prompt)
            logger.info(f"Saved request to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save request to file: {e}")

    def save_response(self, agent_name: str, prompt: str):
        """
        Saves a response to a file.
        """
        if not self.workflow_dir:
            logger.error("Request history directory not available. Skipping saving response.")
            return

        file_name = f"{self.call_index:03d}_{agent_name}_response.txt"
        try:
            file_path = self.workflow_dir / file_name
            with open(file_path, 'w') as f:
                f.write(prompt)
            logger.info(f"Saved request to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save response to file: {e}")

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
