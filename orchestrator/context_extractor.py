"""
Context Extractor for Implementer Agent
Provides rich, relevant code context without sending entire files.

Supports three extraction strategies:
1. AST-based (Python-specific, most accurate)
2. Tree-sitter (Language-agnostic, requires tree-sitter)
3. Heuristic (Fast fallback, works for any language)

Switch strategies by changing EXTRACTION_STRATEGY in config.
"""

import os
import re
import ast
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class ExtractionStrategy(Enum):
    """Available context extraction strategies."""
    TREE_SITTER = "tree_sitter"
    AST = "ast"
    HEURISTIC = "heuristic"


@dataclass
class SymbolInfo:
    """Information about a code symbol (function, class, etc.)."""
    type: str  # 'function', 'class', 'method'
    name: str
    lineno: int
    end_lineno: int
    docstring: Optional[str] = None
    decorators: List[str] = None
    methods: List[str] = None  # For classes


@dataclass
class ContextSection:
    """A section of code with metadata."""
    lines: str
    line_start: int
    line_end: int
    symbol: Optional[str] = None
    symbol_type: Optional[str] = None
    reason: Optional[str] = None
    matched_keywords: List[str] = None


@dataclass
class FileContext:
    """Complete context information for a file."""
    file_path: str
    file_exists: bool
    action: str  # 'create', 'update'
    total_lines: Optional[int] = None
    all_symbols: List[str] = None
    relevant_sections: List[ContextSection] = None
    full_content: Optional[str] = None
    strategy: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.relevant_sections:
            result['relevant_sections'] = [asdict(s) for s in self.relevant_sections]
        return result


class ContextExtractor:
    """
    Extract relevant code context for implementer agent.
    
    Supports multiple extraction strategies:
    - tree_sitter: Language-agnostic using tree-sitter parsers
    - ast: Python-specific using AST parsing (most accurate for Python)
    - heuristic: Fast regex/keyword-based (works for any language)
    """
    
    def __init__(
        self,
        strategy: ExtractionStrategy = ExtractionStrategy.TREE_SITTER,
        max_context_lines: int = 50,
        small_file_threshold: int = 5 * 1024  # 5KB
    ):
        """
        Initialize context extractor.
        
        Args:
            strategy: Extraction strategy to use
            max_context_lines: Max lines to include per section
            small_file_threshold: Files smaller than this sent in full
        """
        self.strategy = strategy
        self.max_context_lines = max_context_lines
        self.small_file_threshold = small_file_threshold
    
    def extract_for_task(self, file_path: str, task_description: str) -> FileContext:
        """
        Extract relevant context for a task.
        
        Args:
            file_path: Path to the file
            task_description: Description of the coding task
            
        Returns:
            FileContext object with relevant code sections
        """
        file_exists = os.path.exists(file_path)
        
        if not file_exists:
            return FileContext(
                file_path=file_path,
                file_exists=False,
                action='create',
                all_symbols=[],
                relevant_sections=[],
                strategy='none_file_not_exists'
            )
        
        file_size = os.path.getsize(file_path)
        
        # For tiny files, just send everything
        if file_size < self.small_file_threshold:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return FileContext(
                    file_path=file_path,
                    file_exists=True,
                    action='update',
                    total_lines=len(content.split('\n')),
                    full_content=content,
                    strategy='full_file_small'
                )
        
        # Route to appropriate extraction strategy
        if self.strategy == ExtractionStrategy.TREE_SITTER:
            return self._extract_with_tree_sitter(file_path, task_description)
        elif self.strategy == ExtractionStrategy.AST:
            return self._extract_with_ast(file_path, task_description)
        elif self.strategy == ExtractionStrategy.HEURISTIC:
            return self._extract_with_heuristic(file_path, task_description)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    # =========================================================================
    # STRATEGY 1: TREE-SITTER (Language-agnostic, recommended)
    # =========================================================================
    
    def _extract_with_tree_sitter(self, file_path: str, task: str) -> FileContext:
        """
        Extract context using tree-sitter parser.
        
        Advantages:
        - Works for multiple languages (Python, C++, etc.)
        - Robust to syntax errors
        - Fast parsing
        
        Requires:
        - tree-sitter
        - tree-sitter-python or tree-sitter-cpp
        """
        try:
            from tree_sitter import Language, Parser
            
            # Determine language and load parser
            if file_path.endswith('.py'):
                try:
                    import tree_sitter_python
                    language = Language(tree_sitter_python.language())
                except ImportError:
                    # Fall back to AST for Python if tree-sitter not available
                    return self._extract_with_ast(file_path, task)
            elif file_path.endswith(('.cpp', '.cc', '.h', '.hpp')):
                try:
                    import tree_sitter_cpp
                    language = Language(tree_sitter_cpp.language())
                except ImportError:
                    # Fall back to heuristic
                    return self._extract_with_heuristic(file_path, task)
            else:
                # Unknown language, use heuristic
                return self._extract_with_heuristic(file_path, task)
            
            parser = Parser()
            parser.set_language(language)
            
            with open(file_path, 'rb') as f:
                content = f.read()
                tree = parser.parse(content)
            
            # Extract symbols using tree-sitter queries
            symbols = self._extract_symbols_tree_sitter(tree, content, file_path)
            
            # Find relevant symbols based on task
            keywords = self._extract_keywords(task)
            relevant_symbols = self._match_symbols_to_keywords(symbols, keywords)
            
            # Build context sections
            lines = content.decode('utf-8', errors='ignore').split('\n')
            context_sections = self._build_context_sections(
                lines, relevant_symbols, keywords
            )
            
            return FileContext(
                file_path=file_path,
                file_exists=True,
                action='update',
                total_lines=len(lines),
                all_symbols=[s.name for s in symbols],
                relevant_sections=context_sections,
                strategy='tree_sitter'
            )
            
        except ImportError:
            # Tree-sitter not available, fall back
            if file_path.endswith('.py'):
                return self._extract_with_ast(file_path, task)
            else:
                return self._extract_with_heuristic(file_path, task)
    
    def _extract_symbols_tree_sitter(
        self, tree, content: bytes, file_path: str
    ) -> List[SymbolInfo]:
        """Extract symbols using tree-sitter queries."""
        from tree_sitter import Language
        
        symbols = []
        
        # Define queries based on language
        if file_path.endswith('.py'):
            query_string = """
                (function_definition
                    name: (identifier) @func_name) @function
                (class_definition
                    name: (identifier) @class_name) @class
            """
        elif file_path.endswith(('.cpp', '.cc', '.h', '.hpp')):
            query_string = """
                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @func_name)) @function
                (class_specifier
                    name: (type_identifier) @class_name) @class
            """
        else:
            return symbols
        
        try:
            # This is a simplified example - actual implementation would need
            # proper tree-sitter language objects
            root_node = tree.root_node
            
            # Walk the tree to find function and class definitions
            self._walk_tree_for_symbols(root_node, content, symbols)
            
        except Exception as e:
            # If tree-sitter parsing fails, return empty list
            print(f"Tree-sitter parsing error: {e}")
        
        return symbols
    
    def _walk_tree_for_symbols(self, node, content: bytes, symbols: List[SymbolInfo]):
        """Recursively walk tree-sitter tree to extract symbols."""
        node_type = node.type
        
        if node_type in ('function_definition', 'function_declarator'):
            # Extract function name
            for child in node.children:
                if child.type == 'identifier':
                    name = content[child.start_byte:child.end_byte].decode('utf-8')
                    symbols.append(SymbolInfo(
                        type='function',
                        name=name,
                        lineno=node.start_point[0] + 1,
                        end_lineno=node.end_point[0] + 1
                    ))
                    break
        
        elif node_type in ('class_definition', 'class_specifier'):
            # Extract class name
            for child in node.children:
                if child.type in ('identifier', 'type_identifier'):
                    name = content[child.start_byte:child.end_byte].decode('utf-8')
                    symbols.append(SymbolInfo(
                        type='class',
                        name=name,
                        lineno=node.start_point[0] + 1,
                        end_lineno=node.end_point[0] + 1
                    ))
                    break
        
        # Recurse to children
        for child in node.children:
            self._walk_tree_for_symbols(child, content, symbols)
    
    # =========================================================================
    # STRATEGY 2: AST (Python-specific, most accurate for Python)
    # =========================================================================
    
    def _extract_with_ast(self, file_path: str, task: str) -> FileContext:
        """
        Extract context using Python AST parser.
        
        Advantages:
        - Most accurate for Python files
        - Built-in to Python, no dependencies
        - Extracts docstrings, decorators, etc.
        
        Limitations:
        - Python-only
        - Requires valid syntax
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # File has syntax errors, fall back to heuristic
            return self._extract_with_heuristic(file_path, task)
        
        # Extract all symbols using AST
        symbols = self._extract_symbols_ast(tree)
        
        # Find relevant symbols based on task keywords
        keywords = self._extract_keywords(task)
        relevant_symbols = self._match_symbols_to_keywords(symbols, keywords)
        
        # Build context sections
        lines = content.split('\n')
        context_sections = self._build_context_sections(
            lines, relevant_symbols, keywords
        )
        
        return FileContext(
            file_path=file_path,
            file_exists=True,
            action='update',
            total_lines=len(lines),
            all_symbols=[s.name for s in symbols],
            relevant_sections=context_sections,
            strategy='ast'
        )
    
    def _extract_symbols_ast(self, tree: ast.AST) -> List[SymbolInfo]:
        """Extract all functions and classes using AST."""
        symbols = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append(SymbolInfo(
                    type='function',
                    name=node.name,
                    lineno=node.lineno,
                    end_lineno=node.end_lineno,
                    docstring=ast.get_docstring(node),
                    decorators=[
                        d.id for d in node.decorator_list
                        if isinstance(d, ast.Name)
                    ]
                ))
            
            elif isinstance(node, ast.ClassDef):
                methods = [
                    n.name for n in node.body
                    if isinstance(n, ast.FunctionDef)
                ]
                
                symbols.append(SymbolInfo(
                    type='class',
                    name=node.name,
                    lineno=node.lineno,
                    end_lineno=node.end_lineno,
                    docstring=ast.get_docstring(node),
                    decorators=[
                        d.id for d in node.decorator_list
                        if isinstance(d, ast.Name)
                    ],
                    methods=methods
                ))
        
        return symbols
    
    # =========================================================================
    # STRATEGY 3: HEURISTIC (Fast, works for any language)
    # =========================================================================
    
    def _extract_with_heuristic(self, file_path: str, task: str) -> FileContext:
        """
        Extract context using simple heuristics.
        
        Advantages:
        - Works for any language
        - No dependencies
        - Fast
        
        Limitations:
        - Less precise
        - May miss context
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        keywords = self._extract_keywords(task)
        
        # Extract simple symbols using regex
        symbols = self._extract_symbols_heuristic(lines)
        
        # Find lines containing keywords
        keyword_matches = []
        for i, line in enumerate(lines):
            matched_kws = [kw for kw in keywords if kw in line.lower()]
            if matched_kws:
                keyword_matches.append((i, matched_kws))
        
        # Build context sections around matches
        context_sections = []
        processed_ranges = set()
        
        for match_idx, matched_kws in keyword_matches[:5]:  # Max 5 matches
            start = max(0, match_idx - 10)
            end = min(len(lines), match_idx + 10)
            
            # Avoid duplicate ranges
            range_key = (start, end)
            if range_key in processed_ranges:
                continue
            processed_ranges.add(range_key)
            
            context_sections.append(ContextSection(
                lines=''.join(lines[start:end]),
                line_start=start + 1,
                line_end=end + 1,
                reason='keyword_match',
                matched_keywords=matched_kws
            ))
        
        # If no matches, provide file start and end
        if not context_sections:
            context_sections = [
                ContextSection(
                    lines=''.join(lines[:25]),
                    line_start=1,
                    line_end=min(25, len(lines)),
                    reason='file_start'
                ),
                ContextSection(
                    lines=''.join(lines[-25:]),
                    line_start=max(1, len(lines) - 24),
                    line_end=len(lines),
                    reason='file_end'
                )
            ]
        
        return FileContext(
            file_path=file_path,
            file_exists=True,
            action='update',
            total_lines=len(lines),
            all_symbols=[s.name for s in symbols],
            relevant_sections=context_sections,
            strategy='heuristic'
        )
    
    def _extract_symbols_heuristic(self, lines: List[str]) -> List[SymbolInfo]:
        """Extract symbols using simple regex patterns."""
        symbols = []
        
        for i, line in enumerate(lines):
            # Python/C++ function definitions
            func_match = re.search(r'(?:def|void|int|bool|string)\s+(\w+)\s*\(', line)
            if func_match:
                symbols.append(SymbolInfo(
                    type='function',
                    name=func_match.group(1),
                    lineno=i + 1,
                    end_lineno=i + 1  # Approximate
                ))
            
            # Python/C++ class definitions
            class_match = re.search(r'class\s+(\w+)\s*[\(:]', line)
            if class_match:
                symbols.append(SymbolInfo(
                    type='class',
                    name=class_match.group(1),
                    lineno=i + 1,
                    end_lineno=i + 1  # Approximate
                ))
        
        return symbols
    
    # =========================================================================
    # SHARED UTILITIES
    # =========================================================================
    
    def _extract_keywords(self, task: str) -> List[str]:
        """Extract keywords from task description."""
        stopwords = {
            'add', 'create', 'update', 'modify', 'write', 'implement',
            'function', 'class', 'method', 'file', 'code',
            'to', 'the', 'a', 'an', 'with', 'for', 'in', 'that', 'is',
            'and', 'or', 'of', 'from', 'by', 'at', 'on'
        }
        
        words = task.lower().split()
        keywords = []
        
        for word in words:
            clean = word.strip('.,!?()[]{}')
            if clean and clean not in stopwords and len(clean) > 2:
                keywords.append(clean)
        
        return keywords
    
    def _match_symbols_to_keywords(
        self, symbols: List[SymbolInfo], keywords: List[str]
    ) -> List[SymbolInfo]:
        """Match symbols to task keywords."""
        matches = []
        
        for symbol in symbols:
            # Check name
            if any(kw in symbol.name.lower() for kw in keywords):
                matches.append(symbol)
                continue
            
            # Check docstring if available
            if symbol.docstring:
                if any(kw in symbol.docstring.lower() for kw in keywords):
                    matches.append(symbol)
                    continue
        
        return matches
    
    def _build_context_sections(
        self,
        lines: List[str],
        relevant_symbols: List[SymbolInfo],
        keywords: List[str]
    ) -> List[ContextSection]:
        """Build context sections around relevant symbols."""
        sections = []
        
        for symbol in relevant_symbols:
            # Include some lines before and after the symbol
            start = max(0, symbol.lineno - 6)
            end = min(len(lines), symbol.end_lineno + 6)
            
            sections.append(ContextSection(
                lines='\n'.join(lines[start:end]),
                line_start=start + 1,
                line_end=end + 1,
                symbol=symbol.name,
                symbol_type=symbol.type,
                matched_keywords=[
                    kw for kw in keywords
                    if kw in symbol.name.lower() or
                    (symbol.docstring and kw in symbol.docstring.lower())
                ]
            ))
        
        # If no relevant symbols found, create file outline
        if not sections:
            outline = self._create_file_outline(
                [SymbolInfo(
                    type='function' if s.type == 'function' else 'class',
                    name=s.name,
                    lineno=s.lineno,
                    end_lineno=s.end_lineno
                ) for s in relevant_symbols] if relevant_symbols else []
            )
            
            sections.append(ContextSection(
                lines=outline,
                line_start=1,
                line_end=len(lines),
                reason='file_outline'
            ))
        
        return sections
    
    def _create_file_outline(self, symbols: List[SymbolInfo]) -> str:
        """Create a compact outline of file structure."""
        outline = []
        
        for symbol in symbols:
            if symbol.type == 'class':
                outline.append(f"class {symbol.name}:")
                if symbol.methods:
                    for method in symbol.methods:
                        outline.append(f"    def {method}(...)")
            else:
                outline.append(f"def {symbol.name}(...)")
        
        return '\n'.join(outline) if outline else "# Empty file or no symbols found"


# Convenience function for easy strategy switching
def extract_context(
    file_path: str,
    task_description: str,
    strategy: str = "tree_sitter"
) -> FileContext:
    """
    Extract context with specified strategy.
    
    Args:
        file_path: Path to file
        task_description: Task description
        strategy: 'tree_sitter', 'ast', or 'heuristic'
    
    Returns:
        FileContext object
    """
    strategy_enum = ExtractionStrategy(strategy)
    extractor = ContextExtractor(strategy=strategy_enum)
    return extractor.extract_for_task(file_path, task_description)
