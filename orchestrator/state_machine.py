"""
State machine implementation for orchestrating the coding workflow.
"""
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any
import json
import re
import logging
from datetime import datetime
from pprint import pformat

# Import the new workflow and the agent client
from .implementer_workflow import run_implementer_stage
from .agents_client import AgentsClient

logger = logging.getLogger(__name__)


class State(Enum):
    """Workflow states"""
    IDLE = "idle"
    SCANNING_CODEBASE = "scanning_codebase"
    PLANNING = "planning"
    TEST_AUTHORING = "test_authoring"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    REVIEW = "review"
    REFINING = "refining"
    FINAL_VALIDATION = "final_validation"
    COMMIT = "commit"
    DONE = "done"
    FAILED = "failed"
    ROLLBACK = "rollback"


@dataclass
class WorkflowState:
    """Current workflow state"""
    current_state: State
    current_task: Optional[str] = None
    retry_count: int = 0
    test_results: Optional[Dict] = None
    metrics: Dict[str, Any] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.metrics is None:
            self.metrics = {}
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class ExecutionResult:
    """Result of workflow execution"""
    success: bool
    commit_hash: Optional[str] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = None


class StateMachine:
    """
    Orchestrates the full workflow from user request to committed code.
    """

    MAX_RETRIES = 3
    STATE_FILE = "/state/workflow_state.json"

    def __init__(self, project_path: Path, config: Dict, auto_commit: bool = False):
        self.project_path = project_path
        self.config = config
        self.auto_commit = auto_commit
        self.state = WorkflowState(current_state=State.IDLE)

    def execute(self, request: str) -> ExecutionResult:
        """
        Execute the full workflow for a coding request.
        """
        # Create agent client once to be reused
        agents_client = AgentsClient()
        
        try:
            logger.info("Starting workflow for request: %s", request)
            logger.info("Auto-commit is %s", "ENABLED" if self.auto_commit else "DISABLED")

            self._transition_to(State.SCANNING_CODEBASE)
            codebase_summary = self._scan_codebase()

            self._transition_to(State.PLANNING)
            task_graph = self._plan(request, codebase_summary, agents_client)
            logger.info("Planned task graph:\n%s", json.dumps(task_graph, indent=2))

            if not task_graph.get('tasks'):
                logger.warning("No tasks were planned. Exiting.")
                self._transition_to(State.DONE)
                return ExecutionResult(success=True, metrics=self.state.metrics)

            self._transition_to(State.TEST_AUTHORING)
            tests = self._author_tests(task_graph, agents_client)

            # Process each task
            for task in task_graph['tasks']:
                self.state.current_task = task['id']
                self.state.retry_count = 0 # Reset for validation retries if any

                self._transition_to(State.IMPLEMENTING)
                implementation_result = self._implement(task, agents_client)

                if not implementation_result['success']:
                    self._transition_to(State.ROLLBACK)
                    self._rollback()
                    error_message = f"Task {task['id']} failed implementation. Last error: {implementation_result.get('last_error', 'Unknown')}"
                    raise Exception(error_message)

                # The patch is applied. Now validate.
                self._transition_to(State.VALIDATING)
                validation_result = self._validate(tests)

                if validation_result['passed']:
                    logger.info("Task %s passed validation.", task['id'])
                else:
                    # If validation fails, we rollback and fail the task.
                    # A more robust solution would involve retrying with feedback.
                    logger.error("Task %s failed validation.", task['id'])
                    self._transition_to(State.ROLLBACK)
                    self._rollback()
                    raise Exception(f"Task {task['id']} failed validation: {validation_result['failures']}")

            # Refine if configured
            if self.config.get('enable_refining', False):
                logger.warning("Refining step is not yet adapted for the new V4A patch workflow. Skipping.")

            # Commit
            commit_hash = None
            if self.auto_commit:
                logger.info("Auto-committing changes.")
                self._transition_to(State.COMMIT)
                commit_hash = self._commit(task_graph)
            else:
                logger.info("Skipping auto-commit as it is disabled.")

            self._transition_to(State.DONE)

            return ExecutionResult(
                success=True,
                commit_hash=commit_hash,
                metrics=self.state.metrics
            )

        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            self._transition_to(State.FAILED)
            return ExecutionResult(
                success=False,
                error=str(e),
                metrics=self.state.metrics
            )

    def _transition_to(self, new_state: State):
        """Transition to a new state"""
        logger.info(f"State transition: {self.state.current_state.value} -> {new_state.value}")
        self.state.current_state = new_state
        self.state.updated_at = datetime.utcnow().isoformat()
        self._save_state()

    def _scan_codebase(self) -> Dict:
        """Scan existing codebase"""
        from .scanner import CodebaseScanner
        scanner = CodebaseScanner(self.project_path)
        return scanner.scan()

    def _plan(self, request: str, codebase_summary: Dict, agents_client: AgentsClient) -> Dict:
        """Generate task graph using Architect agent"""
        return agents_client.plan(request, codebase_summary)

    def _author_tests(self, task_graph: Dict, agents_client: AgentsClient) -> Dict:
        """Generate tests using Spec Author agent"""
        return agents_client.author_tests(task_graph)
    
    def _extract_filepath_from_task(self, task: Dict) -> str:
        """
        Extracts a file path from the task description or acceptance criteria.
        This is a temporary solution and should be improved by making the planning
        agent return structured file paths.
        """
        # Combine description and criteria for a better search
        search_text = task.get('description', '') + ' ' + task.get('acceptance_criteria', '')
        
        # Regex to find file paths (e.g., `path/to/file.py`, `/abs/path/file.py`)
        # It looks for paths enclosed in quotes, backticks, or whitespace.
        match = re.search(r'["\`"]((?:/?\w+)+/\w+\.\w+)["\`"]?', search_text)
        
        if match:
            path = match.group(1)
            logger.info(f"Extracted file path '{path}' from task '{task.get('id')}'.")
            return path

        raise ValueError(f"Could not extract file path from task: {task.get('id')}")

    def _implement(self, task: Dict, agents_client: AgentsClient) -> Dict:
        """Implement task using the new V4A patch workflow."""
        try:
            # Extract file path and run the implementer stage
            #file_path = self._extract_filepath_from_task(task)
            file_path = ''
            return run_implementer_stage(task, file_path, agents_client, self.config.get('config_path', 'config/config.yaml'))
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Could not run implementer stage for task {task.get('id')}: {e}")
            return {'success': False, 'last_error': str(e)}

    def _validate(self, tests: Dict) -> Dict:
        """Run tests and quality gates on the modified codebase."""
        from .validators import Validator
        validator = Validator(self.project_path)
        result = validator.validate(tests)
        logger.info("Validation result:\n%s", pformat(result))
        return result

    def _review(self, validation_result: Dict, agents_client: AgentsClient) -> Dict:
        """Get suggestions from Reviewer agent"""
        return agents_client.review(validation_result)

    def _refine(self, agents_client: AgentsClient) -> str:
        """Refine code using Refiner agent"""
        return agents_client.refine()

    def _rollback(self):
        """Revert changes"""
        logger.info("Rolling back changes.")
        from .git_interface import GitInterface
        git = GitInterface(self.project_path)
        git.rollback()

    def _commit(self, task_graph: Dict) -> str:
        """Commit changes"""
        from .git_interface import GitInterface
        git = GitInterface(self.project_path)
        message = self._generate_commit_message(task_graph)
        logger.info("Committing with message:\n%s", message)
        return git.commit(message)

    def _generate_commit_message(self, task_graph: Dict) -> str:
        """Generate commit message from task metadata"""
        tasks = task_graph.get('tasks', [])
        if not tasks:
            return "Automated commit: No tasks specified."
        summary = f"Implement {len(tasks)} tasks"
        details = "\n".join([f"- {t['description']}" for t in tasks])
        return f"{summary}\n\n{details}"

    def _save_state(self):
        """Persist state to disk"""
        state_dict = asdict(self.state)
        state_dict['current_state'] = self.state.current_state.value

        state_dir = Path(self.project_path) / ".gemini" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        
        state_file = state_dir / "workflow_state.json"

        with open(state_file, 'w') as f:
            json.dump(state_dict, f, indent=2)

    @classmethod
    def load_state(cls, project_path: Path) -> Optional[WorkflowState]:
        """Load persisted state"""
        state_file = project_path / ".gemini" / "state" / "workflow_state.json"
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
                data['current_state'] = State(data['current_state'])
                return WorkflowState(**data)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            logger.error("Could not decode state file. Starting fresh.")
            return None
