"""
V4A Patch Format Parser and Applier

Implements OpenAI's V4A patch format for AI-generated code edits.
Includes robust matching strategies and detailed error reporting.

V4A Format Example:
    *** Begin Patch
    *** Update File: path/to/file.py
    @@ class TargetClass @@
     existing_line
    -old_line
    +new_line
     existing_line
    *** End Patch

Advantages over traditional diffs:
- Uses semantic context (class/function names) instead of line numbers
- Models are specifically trained on this format
- More robust to minor code changes
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class V4AAction(Enum):
    """V4A patch action types."""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"


@dataclass
class V4AHunk:
    """Represents a single V4A patch hunk."""
    action: V4AAction
    file_path: str
    new_path: Optional[str] = None
    context_header: Optional[str] = None
    context_before: List[str] = None
    removed_lines: List[str] = None
    added_lines: List[str] = None
    context_after: List[str] = None
    raw_hunk: str = ""  # For debugging
    
    def __post_init__(self):
        """Initialize list fields if None."""
        if self.context_before is None:
            self.context_before = []
        if self.removed_lines is None:
            self.removed_lines = []
        if self.added_lines is None:
            self.added_lines = []
        if self.context_after is None:
            self.context_after = []


@dataclass
class ApplyResult:
    """Result of applying a hunk."""
    success: bool
    action: str
    file_path: str
    line_range: Optional[Tuple[int, int]] = None
    match_strategy: Optional[str] = None
    error: Optional[str] = None
    suggestions: List[Dict] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class V4APatchParser:
    """Parse V4A format patches into structured hunks."""
    
    def parse(self, patch_text: str) -> List[V4AHunk]:
        """
        Parse V4A patch text into hunks.
        
        Args:
            patch_text: V4A formatted patch string
            
        Returns:
            List of V4AHunk objects
            
        Raises:
            ValueError: If patch format is invalid
        """
        if not patch_text.strip().startswith('*** Begin Patch'):
            raise ValueError("Invalid V4A patch: missing '*** Begin Patch' marker")
        
        if not patch_text.strip().endswith('*** End Patch'):
            raise ValueError("Invalid V4A patch: missing '*** End Patch' marker")
        
        hunks = []
        lines = patch_text.split('\n')
        i = 1  # Skip "*** Begin Patch" line
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('*** Add File:'):
                hunk, next_i = self._parse_add_hunk(lines, i)
                hunks.append(hunk)
                i = next_i
            
            elif line.startswith('*** Delete File:'):
                hunk, next_i = self._parse_delete_hunk(lines, i)
                hunks.append(hunk)
                i = next_i
            
            elif line.startswith('*** Update File:'):
                hunk, next_i = self._parse_update_hunk(lines, i)
                hunks.append(hunk)
                i = next_i
            
            elif line.startswith('*** Move File:'):
                hunk, next_i = self._parse_move_hunk(lines, i)
                hunks.append(hunk)
                i = next_i
            
            elif line.startswith('*** End Patch'):
                break
            
            else:
                i += 1
        
        return hunks
    
    def _parse_add_hunk(self, lines: List[str], start: int) -> Tuple[V4AHunk, int]:
        """Parse an Add File hunk."""
        header = lines[start].strip()
        file_path = header.split(':', 1)[1].strip()
        
        added_lines = []
        i = start + 1
        raw_lines = [header]
        
        while i < len(lines):
            line = lines[i]
            raw_lines.append(line)
            
            if line.strip().startswith('***'):
                break
            
            # Lines starting with + are added content
            if line.startswith('+'):
                added_lines.append(line[1:])  # Remove + prefix
            
            i += 1
        
        return V4AHunk(
            action=V4AAction.ADD,
            file_path=file_path,
            added_lines=added_lines,
            raw_hunk='\n'.join(raw_lines)
        ), i
    
    def _parse_delete_hunk(self, lines: List[str], start: int) -> Tuple[V4AHunk, int]:
        """Parse a Delete File hunk."""
        header = lines[start].strip()
        file_path = header.split(':', 1)[1].strip()
        
        return V4AHunk(
            action=V4AAction.DELETE,
            file_path=file_path,
            raw_hunk=header
        ), start + 1
    
    def _parse_update_hunk(self, lines: List[str], start: int) -> Tuple[V4AHunk, int]:
        """Parse an Update File hunk."""
        header = lines[start].strip()
        file_path = header.split(':', 1)[1].strip()
        
        i = start + 1
        context_header = None
        context_before = []
        removed_lines = []
        added_lines = []
        context_after = []
        current_section = 'before'
        raw_lines = [header]
        
        while i < len(lines):
            line = lines[i]
            raw_lines.append(line)
            
            if line.strip().startswith('***'):
                break
            
            # Context header: @@ class MyClass @@
            if line.strip().startswith('@@') and line.strip().endswith('@@'):
                context_header = line.strip()
                i += 1
                continue
            
            # Context line (unchanged)
            if line.startswith(' '):
                if current_section == 'before':
                    context_before.append(line[1:])
                elif current_section == 'after':
                    context_after.append(line[1:])
            
            # Removed line
            elif line.startswith('-'):
                removed_lines.append(line[1:])
                current_section = 'changes'
            
            # Added line
            elif line.startswith('+'):
                added_lines.append(line[1:])
                current_section = 'changes'
                # After we see changes, next context is 'after'
                if not context_after:
                    current_section = 'after'
            
            i += 1
        
        return V4AHunk(
            action=V4AAction.UPDATE,
            file_path=file_path,
            context_header=context_header,
            context_before=context_before,
            removed_lines=removed_lines,
            added_lines=added_lines,
            context_after=context_after,
            raw_hunk='\n'.join(raw_lines)
        ), i
    
    def _parse_move_hunk(self, lines: List[str], start: int) -> Tuple[V4AHunk, int]:
        """Parse a Move File hunk."""
        header = lines[start].strip()
        # Format: *** Move File: old/path.py -> new/path.py
        paths = header.split(':', 1)[1].strip()
        old_path, new_path = paths.split('->', 1)
        
        return V4AHunk(
            action=V4AAction.MOVE,
            file_path=old_path.strip(),
            new_path=new_path.strip(),
            raw_hunk=header
        ), start + 1


class V4APatchApplier:
    """
    Apply V4A patches with robust matching strategies.
    
    Matching strategies (in order of preference):
    1. Exact match
    2. Fuzzy match (normalized whitespace)
    3. Context-header based search
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize applier.
        
        Args:
            verbose: Print detailed matching information
        """
        self.verbose = verbose
        self.parser = V4APatchParser()
        logger.setLevel(logging.DEBUG)
        logger.debug(f"V4APatchApplier initialized with verbose={verbose}. Logger level set to DEBUG.")
    
    def apply_patch(self, patch_text: str, dry_run: bool = False) -> Dict:
        """
        Apply a V4A patch.
        
        Args:
            patch_text: V4A formatted patch
            dry_run: If True, validate but don't modify files
            
        Returns:
            Dict with success status and detailed results
        """
        results = {
            'success': True,
            'operations': [],
            'errors': []
        }
        
        try:
            hunks = self.parser.parse(patch_text)
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Parse error: {e}")
            return results
        
        logger.debug(f"Number of V4A hunks: {len(hunks)}")
        for index, hunk in enumerate(hunks):
            logger.debug(f"Applying V4A hunk {index}:\n{hunk.file_path}")
            try:
                if hunk.action == V4AAction.ADD:
                    result = self._apply_add(hunk, dry_run)
                elif hunk.action == V4AAction.UPDATE:
                    result = self._apply_update(hunk, dry_run)
                elif hunk.action == V4AAction.DELETE:
                    result = self._apply_delete(hunk, dry_run)
                elif hunk.action == V4AAction.MOVE:
                    result = self._apply_move(hunk, dry_run)
                
                results['operations'].append(result)
                
                if not result.success:
                    results['success'] = False
            
            except Exception as e:
                error_msg = f"Error applying {hunk.action.value} to {hunk.file_path}: {e}"
                results['success'] = False
                results['errors'].append(error_msg)
                results['operations'].append(ApplyResult(
                    success=False,
                    action=hunk.action.value,
                    file_path=hunk.file_path,
                    error=str(e)
                ))
        
        return results
    
    def _apply_add(self, hunk: V4AHunk, dry_run: bool) -> ApplyResult:
        """Apply an Add File operation."""
        if os.path.exists(hunk.file_path):
            return ApplyResult(
                success=False,
                action='add',
                file_path=hunk.file_path,
                error='File already exists'
            )
        logger.debug(f"Hunk added lines:\n{hunk.added_lines}")
        
        if not dry_run:
            # Create parent directories if needed
            os.makedirs(os.path.dirname(hunk.file_path), exist_ok=True)
            
            with open(hunk.file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(hunk.added_lines))
        
        return ApplyResult(
            success=True,
            action='add',
            file_path=hunk.file_path,
            match_strategy='new_file'
        )
    
    def _apply_delete(self, hunk: V4AHunk, dry_run: bool) -> ApplyResult:
        """Apply a Delete File operation."""
        if not os.path.exists(hunk.file_path):
            return ApplyResult(
                success=False,
                action='delete',
                file_path=hunk.file_path,
                error='File does not exist'
            )
        
        if not dry_run:
            os.remove(hunk.file_path)
        
        return ApplyResult(
            success=True,
            action='delete',
            file_path=hunk.file_path,
            match_strategy='file_delete'
        )
    
    def _apply_move(self, hunk: V4AHunk, dry_run: bool) -> ApplyResult:
        """Apply a Move File operation."""
        if not os.path.exists(hunk.file_path):
            return ApplyResult(
                success=False,
                action='move',
                file_path=hunk.file_path,
                error='Source file does not exist'
            )
        
        if os.path.exists(hunk.new_path):
            return ApplyResult(
                success=False,
                action='move',
                file_path=hunk.file_path,
                error=f'Destination {hunk.new_path} already exists'
            )
        
        if not dry_run:
            os.makedirs(os.path.dirname(hunk.new_path), exist_ok=True)
            os.rename(hunk.file_path, hunk.new_path)
        
        return ApplyResult(
            success=True,
            action='move',
            file_path=hunk.file_path,
            match_strategy='file_move'
        )
    
    def _apply_update(self, hunk: V4AHunk, dry_run: bool) -> ApplyResult:
        """Apply an Update File operation with robust matching."""
        if not os.path.exists(hunk.file_path):
            return ApplyResult(
                success=False,
                action='update',
                file_path=hunk.file_path,
                error='File does not exist',
                suggestions=[{'suggestion': 'Use Add File instead'}]
            )
        
        with open(hunk.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Strategy 1: Exact match
        match_result = self._find_exact_match(lines, hunk)
        
        if not match_result['found']:
            # Strategy 2: Fuzzy match (normalize whitespace)
            match_result = self._find_fuzzy_match(lines, hunk)
        
        if not match_result['found']:
            # Strategy 3: Use context header to narrow search
            if hunk.context_header:
                match_result = self._find_with_context_header(lines, hunk)
        
        if not match_result['found']:
            suggestions = self._suggest_similar_code(lines, hunk)
            return ApplyResult(
                success=False,
                action='update',
                file_path=hunk.file_path,
                error='Could not locate code to replace',
                suggestions=suggestions
            )
        
        # Apply the change
        if not dry_run:
            new_lines = (
                lines[:match_result['start_line']] +
                hunk.added_lines +
                lines[match_result['end_line']:]
            )
            
            with open(hunk.file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
        
        return ApplyResult(
            success=True,
            action='update',
            file_path=hunk.file_path,
            line_range=(match_result['start_line'], match_result['end_line']),
            match_strategy=match_result['strategy']
        )
    
    def _find_exact_match(self, lines: List[str], hunk: V4AHunk) -> Dict:
        """Find exact match for removed lines."""
        if not hunk.removed_lines:
            return {'found': False}
        
        search_lines = hunk.removed_lines
        
        for i in range(len(lines) - len(search_lines) + 1):
            if lines[i:i + len(search_lines)] == search_lines:
                if self.verbose:
                    print(f"Exact match found at lines {i}-{i + len(search_lines)}")
                return {
                    'found': True,
                    'start_line': i,
                    'end_line': i + len(search_lines),
                    'strategy': 'exact'
                }
        
        return {'found': False}
    
    def _find_fuzzy_match(self, lines: List[str], hunk: V4AHunk) -> Dict:
        """Fuzzy match allowing whitespace differences."""
        if not hunk.removed_lines:
            return {'found': False}
        
        def normalize(line: str) -> str:
            """Normalize whitespace for comparison."""
            return ' '.join(line.split())
        
        search_normalized = [normalize(l) for l in hunk.removed_lines]
        
        for i in range(len(lines) - len(search_normalized) + 1):
            candidate = [normalize(l) for l in lines[i:i + len(search_normalized)]]
            if candidate == search_normalized:
                if self.verbose:
                    print(f"Fuzzy match found at lines {i}-{i + len(search_normalized)}")
                return {
                    'found': True,
                    'start_line': i,
                    'end_line': i + len(search_normalized),
                    'strategy': 'fuzzy'
                }
        
        return {'found': False}
    
    def _find_with_context_header(self, lines: List[str], hunk: V4AHunk) -> Dict:
        """Use @@ context header to narrow search space."""
        if not hunk.context_header:
            return {'found': False}
        
        # Parse context header: "@@ class MyClass @@" or "@@ def my_function @@"
        match = re.search(r'@@\s*(\w+)\s+(\w+)', hunk.context_header)
        if not match:
            return {'found': False}
        
        entity_type = match.group(1)  # 'class' or 'def'
        entity_name = match.group(2)
        
        # Find the entity definition
        pattern = rf'^\s*{entity_type}\s+{entity_name}'
        start_idx = None
        
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                start_idx = i
                break
        
        if start_idx is None:
            return {'found': False}
        
        # Search within a window after the entity definition
        window_size = 100
        window_lines = lines[start_idx:start_idx + window_size]
        
        # Try exact match within window
        for i in range(len(window_lines) - len(hunk.removed_lines) + 1):
            if window_lines[i:i + len(hunk.removed_lines)] == hunk.removed_lines:
                if self.verbose:
                    print(f"Context-based match found at lines {start_idx + i}-{start_idx + i + len(hunk.removed_lines)}")
                return {
                    'found': True,
                    'start_line': start_idx + i,
                    'end_line': start_idx + i + len(hunk.removed_lines),
                    'strategy': 'context_header'
                }
        
        return {'found': False}
    
    def _suggest_similar_code(self, lines: List[str], hunk: V4AHunk) -> List[Dict]:
        """Suggest similar code sections for debugging."""
        if not hunk.removed_lines:
            return []
        
        # Extract key tokens from removed lines
        key_tokens = set()
        for line in hunk.removed_lines:
            tokens = re.findall(r'\w+', line)
            key_tokens.update(t for t in tokens if len(t) > 3)
        
        if not key_tokens:
            return []
        
        suggestions = []
        for i, line in enumerate(lines):
            line_tokens = set(re.findall(r'\w+', line))
            overlap = len(key_tokens & line_tokens)
            
            if overlap >= len(key_tokens) * 0.4:  # 40% token overlap
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                suggestions.append({
                    'line': i + 1,
                    'context': '\n'.join(lines[context_start:context_end]),
                    'overlap_tokens': list(key_tokens & line_tokens),
                    'overlap_ratio': overlap / len(key_tokens)
                })
        
        # Sort by overlap ratio and return top suggestions
        suggestions.sort(key=lambda x: x['overlap_ratio'], reverse=True)
        return suggestions[:3]


def validate_patch(patch_text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate V4A patch format without applying.
    
    Args:
        patch_text: V4A patch string
        
    Returns:
        (is_valid, error_message)
    """
    try:
        parser = V4APatchParser()
        parser.parse(patch_text)
        return True, None
    except Exception as e:
        return False, str(e)
