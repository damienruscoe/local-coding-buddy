"""
Codebase scanner for analyzing existing projects.
"""
import os
from pathlib import Path
from typing import Dict, List, Set
import logging
import subprocess
import json

logger = logging.getLogger(__name__)


class CodebaseScanner:
    """
    Scans existing codebases to produce structured summaries
    without requiring LLM context.
    """
    
    IGNORED_DIRS = {
        '.git', '__pycache__', 'node_modules', 'build', 'dist',
        '.pytest_cache', '.venv', 'venv', 'cmake-build-debug'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.py', '.cpp', '.cc', '.cxx', '.hpp', '.h', '.hxx'
    }
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    def scan(self) -> Dict:
        """
        Perform full codebase scan.
        
        Returns structured summary including:
        - File tree
        - Module list
        - Build targets
        - Public APIs
        - Dependency graph
        """
        logger.info(f"Scanning codebase at {self.project_path}")
        
        summary = {
            'file_count': 0,
            'modules': [],
            'build_targets': [],
            'dependencies': {},
            'api_surface': {}
        }
        
        # File tree analysis
        files = self._walk_files()
        summary['file_count'] = len(files)
        
        # Language-specific analysis
        py_files = [f for f in files if f.suffix == '.py']
        cpp_files = [f for f in files if f.suffix in {'.cpp', '.cc', '.cxx'}]
        
        if py_files:
            summary['modules'].extend(self._analyze_python_modules(py_files))
        
        if cpp_files:
            summary['build_targets'].extend(self._analyze_cpp_targets())
        
        # Extract dependencies
        summary['dependencies'] = self._extract_dependencies(files)
        
        logger.info(f"Scan complete: {summary['file_count']} files, "
                   f"{len(summary['modules'])} modules")
        
        return summary
    
    def _walk_files(self) -> List[Path]:
        """Walk directory tree and collect source files"""
        files = []
        
        for root, dirs, filenames in os.walk(self.project_path):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]
            
            for filename in filenames:
                filepath = Path(root) / filename
                if filepath.suffix in self.SUPPORTED_EXTENSIONS:
                    files.append(filepath)
        
        return files
    
    def _analyze_python_modules(self, py_files: List[Path]) -> List[Dict]:
        """Extract Python module information"""
        modules = []
        
        for py_file in py_files:
            relative_path = py_file.relative_to(self.project_path)
            module_name = str(relative_path.with_suffix('')).replace(os.sep, '.')
            
            # Extract public API (classes and functions)
            api = self._extract_python_api(py_file)
            
            modules.append({
                'name': module_name,
                'path': str(relative_path),
                'api': api
            })
        
        return modules
    
    def _extract_python_api(self, py_file: Path) -> List[str]:
        """Extract public classes and functions from Python file"""
        api = []
        
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Simple regex-based extraction (can be enhanced with AST)
            import re
            
            # Find class definitions
            classes = re.findall(r'^class\s+([A-Za-z_][A-Za-z0-9_]*)', content, re.MULTILINE)
            api.extend([f"class {c}" for c in classes if not c.startswith('_')])
            
            # Find function definitions
            functions = re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)', content, re.MULTILINE)
            api.extend([f"def {f}" for f in functions if not f.startswith('_')])
            
        except Exception as e:
            logger.warning(f"Failed to parse {py_file}: {e}")
        
        return api
    
    def _analyze_cpp_targets(self) -> List[Dict]:
        """Extract C++ build targets from CMakeLists.txt"""
        targets = []
        
        cmake_files = list(self.project_path.glob('**/CMakeLists.txt'))
        
        for cmake_file in cmake_files:
            try:
                with open(cmake_file, 'r') as f:
                    content = f.read()
                
                # Extract add_executable and add_library calls
                import re
                executables = re.findall(r'add_executable\s*\(\s*(\w+)', content)
                libraries = re.findall(r'add_library\s*\(\s*(\w+)', content)
                
                for exe in executables:
                    targets.append({'name': exe, 'type': 'executable'})
                
                for lib in libraries:
                    targets.append({'name': lib, 'type': 'library'})
                    
            except Exception as e:
                logger.warning(f"Failed to parse {cmake_file}: {e}")
        
        return targets
    
    def _extract_dependencies(self, files: List[Path]) -> Dict[str, List[str]]:
        """Build dependency graph"""
        dependencies = {}
        
        for file in files:
            deps = set()
            
            try:
                with open(file, 'r') as f:
                    content = f.read()
                
                if file.suffix == '.py':
                    # Extract Python imports
                    import re
                    imports = re.findall(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE)
                    deps.update(imports)
                
                elif file.suffix in {'.cpp', '.cc', '.cxx', '.hpp', '.h'}:
                    # Extract C++ includes
                    import re
                    includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', content)
                    deps.update(includes)
                
                if deps:
                    relative_path = str(file.relative_to(self.project_path))
                    dependencies[relative_path] = list(deps)
                    
            except Exception as e:
                logger.warning(f"Failed to extract dependencies from {file}: {e}")
        
        return dependencies
