"""
Git integration for version control operations.
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GitInterface:
    """
    Handles all git operations: commits, rollbacks, branching.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self._ensure_git_repo()
    
    def _ensure_git_repo(self):
        """Ensure project is a git repository"""
        if not (self.project_path / '.git').exists():
            logger.info("Initializing git repository")
            self._run_git(['init'])
    
    def create_branch(self, branch_name: str):
        """Create and checkout a new branch"""
        logger.info(f"Creating branch: {branch_name}")
        self._run_git(['checkout', '-b', branch_name])
    
    def commit(self, message: str) -> str:
        """
        Commit current changes.
        
        Returns:
            Commit hash
        """
        logger.info("Committing changes")
        
        # Stage all changes
        self._run_git(['add', '-A'])
        
        # Commit
        self._run_git(['commit', '-m', message])
        
        # Get commit hash
        result = self._run_git(['rev-parse', 'HEAD'])
        commit_hash = result.stdout.decode().strip()
        
        logger.info(f"Committed: {commit_hash}")
        return commit_hash
    
    def rollback(self):
        """Rollback to last committed state"""
        logger.info("Rolling back changes")
        
        # Reset working directory
        self._run_git(['reset', '--hard', 'HEAD'])
        
        # Clean untracked files
        self._run_git(['clean', '-fd'])
    
    def get_diff(self) -> str:
        """Get current diff"""
        result = self._run_git(['diff', 'HEAD'])
        return result.stdout.decode()
    
    def apply_patch(self, patch: str):
        """Apply a patch"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.patch') as f:
            f.write(patch)
            patch_file = f.name
        
        try:
            self._run_git(['apply', patch_file])
        finally:
            import os
            os.unlink(patch_file)
    
    def _run_git(self, args: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run git command"""
        cmd = ['git'] + args
        
        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            check=check,
            timeout=30
        )
        
        if check and result.returncode != 0:
            error = result.stderr.decode()
            logger.error(f"Git command failed: {error}")
            raise subprocess.CalledProcessError(result.returncode, cmd, stderr=error)
        
        return result
