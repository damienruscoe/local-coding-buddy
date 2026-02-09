"""
Implementer Stage Integration

Integrates context extraction and V4A patch application into the workflow.
"""

import os
import yaml
from typing import Dict, Optional
from .context_extractor import ContextExtractor, ExtractionStrategy, FileContext
from .v4a_patch import V4APatchApplier, ApplyResult


class ImplementerStage:
    """
    Manages the implementer stage with rich context and V4A patches.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize implementer stage.
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize context extractor with configured strategy
        strategy_name = self.config.get('context_extraction_strategy', 'tree_sitter')
        strategy = ExtractionStrategy(strategy_name)
        
        self.context_extractor = ContextExtractor(
            strategy=strategy,
            max_context_lines=self.config.get('max_context_lines', 50),
            small_file_threshold=self.config.get('small_file_threshold', 5120)
        )
        
        # Initialize patch applier
        self.patch_applier = V4APatchApplier(
            verbose=self.config.get('patch_verbose', False)
        )
        
        self.max_retries = self.config.get('max_retries', 3)
    
    def run_implementer(
        self,
        task: Dict,
        file_path: str,
        agents_client  # Import to avoid circular dependency
    ) -> Dict:
        """
        Execute implementer stage with context and V4A patches.
        
        Args:
            task: Task specification
            file_path: Target file path
            agents_client: Client for calling LLM agents
            
        Returns:
            Result dictionary with success status and details
        """
        # Step 1: Extract rich context
        context = self.context_extractor.extract_for_task(
            file_path, task['description']
        )
        
        # Step 2: Prepare implementer input
        implementer_input = self._prepare_implementer_input(task, context)
        
        # Step 3: Call implementer with retries
        for attempt in range(self.max_retries):
            # Build prompt for the agent
            prompt = self._build_prompt_from_input(implementer_input)
            
            # Call LLM agent using the existing client method
            response_data = agents_client._call_agent(
                agent_type='implementer',
                prompt=prompt
            )
            raw_output = response_data.get('text', '')

            # Extract the patch content, ignoring conversational text and markdown.
            try:
                start_index = raw_output.index('*** Begin Patch')
                end_index = raw_output.rindex('*** End Patch') + len('*** End Patch')
                patch_output = raw_output[start_index:end_index]
            except ValueError:
                # Delimiters not found. The response is probably an error or invalid.
                # Pass the raw output to the applier, which will fail and report an error.
                patch_output = raw_output
            
            # Step 4: Validate patch (dry run)
            dry_run_result = self.patch_applier.apply_patch(
                patch_output,
                dry_run=True
            )
            
            if dry_run_result['success']:
                # Step 5: Apply patch for real
                apply_result = self.patch_applier.apply_patch(
                    patch_output,
                    dry_run=False
                )
                
                return {
                    'success': True,
                    'attempt': attempt + 1,
                    'context_strategy': context.strategy,
                    'operations': apply_result['operations']
                }
            else:
                # Retry with feedback
                implementer_input = self._prepare_retry_input(
                    implementer_input,
                    patch_output,
                    dry_run_result
                )
        
        # All retries failed
        return {
            'success': False,
            'attempts': self.max_retries,
            'last_error': dry_run_result.get('errors', ['Unknown error']),
            'context_strategy': context.strategy
        }

    def _build_prompt_from_input(self, implementer_input: Dict) -> str:
        """Builds a string prompt from the structured input dictionary."""
        
        task = implementer_input['task']
        file_context = implementer_input['file_context']
        instructions = implementer_input['instructions']
        
        prompt = f"""{instructions}

**IMPORTANT**: Your response MUST contain ONLY the V4A patch, starting with `*** Begin Patch` and ending with `*** End Patch`. Do not include any other text, comments, or explanations before or after the patch.

**Task**: {task.get('description', 'N/A')}

**Acceptance Criteria**:
{chr(10).join([f"- {c}" for c in task.get('acceptance_criteria', [])])}
"""

        if file_context.get('content'):
            prompt += f"""
**File Context for `{file_context['file_path']}`**:
```
{file_context['content']}
```
"""
        
        if 'previous_attempt' in implementer_input:
            prompt += f"""
**Your previous attempt failed with these errors**: {implementer_input.get('errors', 'N/A')}

**This was the patch that failed**:
```
{implementer_input['previous_attempt']}
```

Please analyze the errors and the context and provide a corrected V4A patch.
"""
        return prompt
    
    def _prepare_implementer_input(
        self,
        task: Dict,
        context: FileContext
    ) -> Dict:
        """Prepare input for implementer agent."""
        return {
            'task': task,
            'file_context': context.to_dict(),
            'output_format': 'v4a_patch',
            'instructions': self._get_v4a_instructions(),
            'attempt_number': 1
        }
    
    def _prepare_retry_input(
        self,
        previous_input: Dict,
        failed_patch: str,
        errors: Dict
    ) -> Dict:
        """Prepare input for retry with error feedback."""
        return {
            **previous_input,
            'previous_attempt': failed_patch,
            'errors': errors.get('errors', []),
            'suggestions': self._extract_suggestions(errors),
            'attempt_number': previous_input.get('attempt_number', 1) + 1
        }
    
    def _extract_suggestions(self, errors: Dict) -> list:
        """Extract actionable suggestions from error results."""
        suggestions = []
        
        for op in errors.get('operations', []):
            if not op.get('success') and op.get('suggestions'):
                suggestions.extend(op['suggestions'])
        
        return suggestions
    
    def _get_v4a_instructions(self) -> str:
        """Get V4A format instructions for the agent."""
        return """
Use V4A patch format for all file operations.

FORMAT SPECIFICATION:

For creating new files:
*** Begin Patch
*** Add File: path/to/file.py
+def new_function():
+    return "Hello"
*** End Patch

For updating existing files:
*** Begin Patch
*** Update File: path/to/file.py
@@ class TargetClass @@
 existing_line_before
-old_line_to_remove
+new_line_to_add
 existing_line_after
*** End Patch

For deleting files:
*** Begin Patch
*** Delete File: path/to/file.py
*** End Patch

IMPORTANT RULES:
1. Always use @@ markers with class or function names for context
2. Include 2-3 lines of unchanged code before and after changes
3. NEVER use line numbers - rely on code context only
4. Lines starting with ' ' (space) are context (unchanged)
5. Lines starting with '-' are removed
6. Lines starting with '+' are added

EXAMPLE:
*** Begin Patch
*** Update File: calculator.py
@@ def add @@
 def add(a, b):
-    return a + b
+    \"\"\"Add two numbers.\"\"\"
+    return a + b
 
*** End Patch

This format allows the system to find and replace code based on content,
not brittle line numbers.
"""


class ImplementerWorkflow:
    """
    Complete workflow for implementer stage.
    
    Example usage:
        workflow = ImplementerWorkflow()
        result = workflow.execute(task, file_path, agents_client)
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize workflow."""
        self.stage = ImplementerStage(config_path)
    
    def execute(
        self,
        task: Dict,
        file_path: str,
        agents_client
    ) -> Dict:
        """
        Execute complete implementer workflow.
        
        Returns complete result including:
        - Success status
        - Number of attempts
        - Context extraction strategy used
        - Applied operations
        - Any errors
        """
        return self.stage.run_implementer(task, file_path, agents_client)


# Convenience function for direct use
def run_implementer_stage(
    task: Dict,
    file_path: str,
    agents_client,
    config_path: str = "config/config.yaml"
) -> Dict:
    """
    Convenience function to run implementer stage.
    
    Args:
        task: Task specification
        file_path: Target file path
        agents_client: Agent communication client
        config_path: Path to config file
        
    Returns:
        Result dictionary
    """
    workflow = ImplementerWorkflow(config_path)
    return workflow.execute(task, file_path, agents_client)
