"""
State machine implementation for orchestrating the coding workflow.
"""
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime

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
        try:
            logger.info(f"Starting workflow for request: {request}")
            
            # State transitions
            self._transition_to(State.SCANNING_CODEBASE)
            codebase_summary = self._scan_codebase()
            
            self._transition_to(State.PLANNING)
            task_graph = self._plan(request, codebase_summary)
            
            self._transition_to(State.TEST_AUTHORING)
            tests = self._author_tests(task_graph)
            
            # Process each task
            for task in task_graph['tasks']:
                self.state.current_task = task['id']
                self.state.retry_count = 0
                
                while self.state.retry_count < self.MAX_RETRIES:
                    self._transition_to(State.IMPLEMENTING)
                    code_diff = self._implement(task)
                    
                    self._transition_to(State.VALIDATING)
                    validation_result = self._validate(code_diff, tests)
                    
                    if validation_result['passed']:
                        break
                    else:
                        self.state.retry_count += 1
                        if self.state.retry_count >= self.MAX_RETRIES:
                            self._transition_to(State.ROLLBACK)
                            self._rollback()
                            raise Exception(f"Task {task['id']} failed after {self.MAX_RETRIES} retries")
                        
                        self._transition_to(State.REVIEW)
                        suggestions = self._review(validation_result)
                        task['suggestions'] = suggestions
            
            # Refine if configured
            if self.config.get('enable_refining', False):
                self._transition_to(State.REFINING)
                refined_diff = self._refine()
                
                self._transition_to(State.FINAL_VALIDATION)
                final_result = self._validate(refined_diff, tests)
                
                if not final_result['passed']:
                    self._transition_to(State.ROLLBACK)
                    self._rollback()
                    raise Exception("Final validation failed after refining")
            
            # Commit
            commit_hash = None
            if self.auto_commit:
                self._transition_to(State.COMMIT)
                commit_hash = self._commit(task_graph)
            
            self._transition_to(State.DONE)
            
            return ExecutionResult(
                success=True,
                commit_hash=commit_hash,
                metrics=self.state.metrics
            )
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
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
    
    def _plan(self, request: str, codebase_summary: Dict) -> Dict:
        """Generate task graph using Architect agent"""
        from .agents_client import AgentsClient
        client = AgentsClient()
        return client.plan(request, codebase_summary)
    
    def _author_tests(self, task_graph: Dict) -> Dict:
        """Generate tests using Spec Author agent"""
        from .agents_client import AgentsClient
        client = AgentsClient()
        return client.author_tests(task_graph)
    
    def _implement(self, task: Dict) -> str:
        """Implement task using Implementer agent"""
        from .agents_client import AgentsClient
        client = AgentsClient()
        return client.implement(task)
    
    def _validate(self, code_diff: str, tests: Dict) -> Dict:
        """Run tests and quality gates"""
        from .validators import Validator
        validator = Validator(self.project_path)
        return validator.validate(code_diff, tests)
    
    def _review(self, validation_result: Dict) -> Dict:
        """Get suggestions from Reviewer agent"""
        from .agents_client import AgentsClient
        client = AgentsClient()
        return client.review(validation_result)
    
    def _refine(self) -> str:
        """Refine code using Refiner agent"""
        from .agents_client import AgentsClient
        client = AgentsClient()
        return client.refine()
    
    def _rollback(self):
        """Revert changes"""
        from .git_interface import GitInterface
        git = GitInterface(self.project_path)
        git.rollback()
    
    def _commit(self, task_graph: Dict) -> str:
        """Commit changes"""
        from .git_interface import GitInterface
        git = GitInterface(self.project_path)
        message = self._generate_commit_message(task_graph)
        return git.commit(message)
    
    def _generate_commit_message(self, task_graph: Dict) -> str:
        """Generate commit message from task metadata"""
        tasks = task_graph['tasks']
        summary = f"Implement {len(tasks)} tasks"
        details = "\n".join([f"- {t['description']}" for t in tasks])
        return f"{summary}\n\n{details}"
    
    def _save_state(self):
        """Persist state to disk"""
        state_dict = asdict(self.state)
        state_dict['current_state'] = self.state.current_state.value
        
        with open(self.STATE_FILE, 'w') as f:
            json.dump(state_dict, f, indent=2)
    
    @classmethod
    def load_state(cls) -> Optional[WorkflowState]:
        """Load persisted state"""
        try:
            with open(cls.STATE_FILE, 'r') as f:
                data = json.load(f)
                data['current_state'] = State(data['current_state'])
                return WorkflowState(**data)
        except FileNotFoundError:
            return None
