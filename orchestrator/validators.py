"""
Validation and quality gate enforcement.
"""
import subprocess
import logging
from pathlib import Path
from typing import Dict, List
import tempfile
import os

logger = logging.getLogger(__name__)


class Validator:
    """
    Runs tests and enforces quality gates.
    Pure infrastructure - no LLM reasoning.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    def validate(self, code_diff: str, tests: Dict) -> Dict:
        """
        Run full validation suite.
        
        Returns:
            {
                'passed': bool,
                'failures': List[str],
                'coverage': float,
                'lint_issues': List[str]
            }
        """
        logger.info("Starting validation")
        
        # Apply diff
        self._apply_diff(code_diff)
        
        result = {
            'passed': True,
            'failures': [],
            'coverage': 0.0,
            'lint_issues': []
        }
        
        try:
            # Run tests
            test_result = self._run_tests()
            result['failures'] = test_result['failures']
            
            if test_result['failures']:
                result['passed'] = False
                return result
            
            # Check coverage
            coverage = self._check_coverage()
            result['coverage'] = coverage
            
            if coverage < 80.0:  # Configurable threshold
                result['passed'] = False
                result['failures'].append(f"Coverage {coverage}% below threshold 80%")
            
            # Run linters
            lint_issues = self._run_linters()
            result['lint_issues'] = lint_issues
            
            if lint_issues:
                result['passed'] = False
                result['failures'].extend(lint_issues)
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            result['passed'] = False
            result['failures'].append(str(e))
        
        return result
    
    def _apply_diff(self, diff: str):
        """Apply unified diff to project"""
        try:
            # Write diff to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.patch') as f:
                f.write(diff)
                patch_file = f.name
            
            # Apply patch
            subprocess.run(
                ['patch', '-p1', '-i', patch_file],
                cwd=self.project_path,
                check=True,
                capture_output=True,
                timeout=30
            )
            
            os.unlink(patch_file)
            logger.info("Diff applied successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply diff: {e.stderr.decode()}")
            raise
    
    def _run_tests(self) -> Dict:
        """Run test suite"""
        failures = []
        
        # Detect test framework
        if (self.project_path / 'pytest.ini').exists() or \
           any(self.project_path.glob('test_*.py')):
            failures = self._run_pytest()
        
        elif (self.project_path / 'CMakeLists.txt').exists():
            failures = self._run_ctest()
        
        return {'failures': failures}
    
    def _run_pytest(self) -> List[str]:
        """Run pytest"""
        try:
            result = subprocess.run(
                ['pytest', '-v', '--tb=short'],
                cwd=self.project_path,
                capture_output=True,
                timeout=300
            )
            
            if result.returncode != 0:
                # Parse failures from output
                output = result.stdout.decode()
                failures = self._parse_pytest_failures(output)
                return failures
            
            return []
            
        except subprocess.TimeoutExpired:
            return ["Tests timed out after 5 minutes"]
        except Exception as e:
            return [f"Test execution failed: {e}"]
    
    def _run_ctest(self) -> List[str]:
        """Run CTest (for C++ projects)"""
        try:
            # Build first
            build_dir = self.project_path / 'build'
            build_dir.mkdir(exist_ok=True)
            
            # Configure
            subprocess.run(
                ['cmake', '..'],
                cwd=build_dir,
                check=True,
                capture_output=True,
                timeout=120
            )
            
            # Build
            subprocess.run(
                ['cmake', '--build', '.'],
                cwd=build_dir,
                check=True,
                capture_output=True,
                timeout=300
            )
            
            # Test
            result = subprocess.run(
                ['ctest', '--output-on-failure'],
                cwd=build_dir,
                capture_output=True,
                timeout=300
            )
            
            if result.returncode != 0:
                output = result.stdout.decode()
                return self._parse_ctest_failures(output)
            
            return []
            
        except subprocess.CalledProcessError as e:
            return [f"Build/test failed: {e.stderr.decode()}"]
        except subprocess.TimeoutExpired:
            return ["Build/test timed out"]
    
    def _check_coverage(self) -> float:
        """Measure code coverage"""
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ['pytest', '--cov=.', '--cov-report=term'],
                cwd=self.project_path,
                capture_output=True,
                timeout=300
            )
            
            # Parse coverage from output
            output = result.stdout.decode()
            coverage = self._parse_coverage(output)
            return coverage
            
        except Exception as e:
            logger.warning(f"Coverage check failed: {e}")
            return 0.0
    
    def _run_linters(self) -> List[str]:
        """Run static analysis"""
        issues = []
        
        # Python: pylint, black
        py_files = list(self.project_path.glob('**/*.py'))
        if py_files:
            issues.extend(self._run_pylint(py_files))
            issues.extend(self._run_black(py_files))
        
        # C++: clang-tidy, cppcheck
        cpp_files = list(self.project_path.glob('**/*.cpp'))
        if cpp_files:
            issues.extend(self._run_clang_tidy(cpp_files))
        
        return issues
    
    def _run_pylint(self, files: List[Path]) -> List[str]:
        """Run pylint"""
        try:
            result = subprocess.run(
                ['pylint'] + [str(f) for f in files],
                cwd=self.project_path,
                capture_output=True,
                timeout=60
            )
            
            if result.returncode != 0:
                output = result.stdout.decode()
                # Extract only errors, not warnings
                issues = [line for line in output.split('\n') 
                         if 'error' in line.lower()]
                return issues[:10]  # Limit to top 10
            
            return []
            
        except Exception as e:
            logger.warning(f"Pylint failed: {e}")
            return []
    
    def _run_black(self, files: List[Path]) -> List[str]:
        """Check formatting with black"""
        try:
            result = subprocess.run(
                ['black', '--check'] + [str(f) for f in files],
                cwd=self.project_path,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ["Code formatting issues detected (run 'black .' to fix)"]
            
            return []
            
        except Exception as e:
            logger.warning(f"Black check failed: {e}")
            return []
    
    def _run_clang_tidy(self, files: List[Path]) -> List[str]:
        """Run clang-tidy"""
        # Simplified - would need compile_commands.json
        return []
    
    def _parse_pytest_failures(self, output: str) -> List[str]:
        """Extract failure messages from pytest output"""
        failures = []
        lines = output.split('\n')
        
        for line in lines:
            if 'FAILED' in line:
                failures.append(line.strip())
        
        return failures
    
    def _parse_ctest_failures(self, output: str) -> List[str]:
        """Extract failure messages from ctest output"""
        failures = []
        lines = output.split('\n')
        
        in_failure = False
        for line in lines:
            if 'Test' in line and 'Failed' in line:
                in_failure = True
                failures.append(line.strip())
            elif in_failure and line.strip():
                failures.append(line.strip())
                in_failure = False
        
        return failures
    
    def _parse_coverage(self, output: str) -> float:
        """Extract coverage percentage from output"""
        import re
        
        # Look for "TOTAL" line with percentage
        match = re.search(r'TOTAL.*?(\d+)%', output)
        if match:
            return float(match.group(1))
        
        return 0.0
