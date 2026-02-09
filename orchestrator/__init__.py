"""
Orchestrator package for local-coding-buddy.

Enhanced with intelligent context extraction and V4A patch format.
"""

from .context_extractor import (
    ContextExtractor,
    ExtractionStrategy,
    extract_context,
    FileContext,
    ContextSection
)

from .v4a_patch import (
    V4APatchParser,
    V4APatchApplier,
    V4AAction,
    V4AHunk,
    ApplyResult,
    validate_patch
)

from .implementer_workflow import (
    ImplementerStage,
    ImplementerWorkflow,
    run_implementer_stage
)

__version__ = "2.0.0"
__all__ = [
    # Context extraction
    'ContextExtractor',
    'ExtractionStrategy',
    'extract_context',
    'FileContext',
    'ContextSection',
    
    # V4A patches
    'V4APatchParser',
    'V4APatchApplier',
    'V4AAction',
    'V4AHunk',
    'ApplyResult',
    'validate_patch',
    
    # Workflow
    'ImplementerStage',
    'ImplementerWorkflow',
    'run_implementer_stage',
]
