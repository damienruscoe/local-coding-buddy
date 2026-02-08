"""
Client for communicating with agent runtime.
"""
import requests
import logging
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AgentsClient:
    """
    Interface to the agent runtime service.
    Handles communication with LLM-based reasoning agents.
    """
    
    AGENT_RUNTIME_URL = "http://agent-runtime:8000"
    
    def __init__(self):
        self.base_url = self.AGENT_RUNTIME_URL
    
    def plan(self, request: str, codebase_summary: Dict) -> Dict:
        """
        Call Architect agent to decompose request into tasks.
        
        Returns:
            Task graph with acceptance criteria
        """
        logger.info("Calling Architect agent for planning")
        
        response = self._call_agent(
            agent_type="architect",
            prompt=self._build_architect_prompt(request, codebase_summary)
        )
        
        return self._parse_task_graph(response)
    
    def author_tests(self, task_graph: Dict) -> Dict:
        """
        Call Spec Author agent to generate tests.
        
        Returns:
            Test definitions
        """
        logger.info("Calling Spec Author agent for test generation")
        
        response = self._call_agent(
            agent_type="spec_author",
            prompt=self._build_test_author_prompt(task_graph)
        )
        
        return self._parse_tests(response)
    
    def implement(self, task: Dict) -> str:
        """Call Implementer agent to generate code."""
        logger.info(f"Calling Implementer agent for task: {task['id']}")
        
        response = self._call_agent(
            agent_type="implementer",
            prompt=self._build_implementer_prompt(task)
        )
        
        raw_text = response.get('text', '')
        
        # The implementer can sometimes wrap the diff in markdown.
        # We need to extract just the raw diff.
        if '```diff' in raw_text:
            try:
                return raw_text.split('```diff')[1].split('```')[0].strip()
            except IndexError:
                # Fallback for malformed markdown
                pass
        
        if '```' in raw_text:
            try:
                # Generic fallback for any fenced code block
                return raw_text.split('```')[1].split('```')[0].strip()
            except IndexError:
                pass

        # If no markers are found, assume the whole response is the diff
        return raw_text.strip()
    
    def review(self, validation_result: Dict) -> Dict:
        """
        Call Reviewer agent for failure analysis.
        
        Returns:
            Suggestions for fixes
        """
        logger.info("Calling Reviewer agent for analysis")
        
        response = self._call_agent(
            agent_type="reviewer",
            prompt=self._build_reviewer_prompt(validation_result)
        )
        
        return response
    
    def refine(self) -> str:
        """
        Call Refiner agent for code improvement.
        
        Returns:
            Refined code diff
        """
        logger.info("Calling Refiner agent for refactoring")
        
        response = self._call_agent(
            agent_type="refiner",
            prompt=self._build_refiner_prompt()
        )
        
        return response.get('text', '')
    
    def _call_agent(self, agent_type: str, prompt: str, 
                    max_tokens: int = 2048, temperature: float = 0.7) -> Dict:
        """
        Make HTTP request to agent runtime.
        """
        logger.debug("Calling agent '%s' with prompt:\n%s", agent_type, prompt)

        payload = {
            'agent_type': agent_type,
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            
            response_json = response.json()
            logger.debug("Agent '%s' returned response:\n%s", agent_type, response_json.get('text', ''))
            return response_json
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Agent call failed: {e}")
            raise
    
    def _build_architect_prompt(self, request: str, codebase_summary: Dict) -> str:
        """Build prompt for Architect agent"""
        return f"""Please decompose the following user request into a task graph.

**User Request**: {request}

**Codebase Summary**:
- Files: {codebase_summary['file_count']}
- Modules: {len(codebase_summary['modules'])}
- Build Targets: {len(codebase_summary['build_targets'])}

Remember to follow all the instructions from your system prompt precisely. Your response must be a markdown document with a single JSON code block containing the task graph.
"""
    
    def _build_test_author_prompt(self, task_graph: Dict) -> str:
        """Build prompt for Spec Author agent"""
        tasks = task_graph.get('tasks', [])
        language = task_graph.get("language")
        task_descriptions = "\n".join([f"- {t['description']}" for t in tasks])

        if not language:
            logger.warning("Language not found in task graph. Test generation might be inaccurate.")
            language_prompt = "You need to infer the language from the tasks."
        else:
            language_prompt = f"The tasks are for a {language} project. Please write tests in {language}."

        return f"""You are an expert test engineer. Your mission is to write a robust suite of tests based on the provided tasks.

{language_prompt}

**Tasks to be Tested:**
{task_descriptions}

**Instructions:**
Your generated tests must adhere to all the guidelines in your system prompt, including:
- Creating robust tests that match the complexity of the unit under test.
- Commenting on key happy-path tests to serve as documentation.
- Using data-driven tests where it improves clarity and reduces duplication.

Generate a complete test file with all necessary imports and boilerplate.
"""
    
    def _build_implementer_prompt(self, task: Dict) -> str:
        """Build prompt for Implementer agent"""
        feedback_context = task.get('feedback')
        suggestions = task.get('suggestions')

        # Base instructions for diff formatting
        diff_formatting_instructions = """
**CRITICAL INSTRUCTIONS FOR DIFF FORMATTING:**
-   Your output MUST be a **pure unified diff**. Do NOT include any comments, introductory text, blank lines, or any other content outside the strict diff format. The diff MUST start directly with `---`.
-   If implementing changes across **multiple files**, concatenate their individual unified diffs directly, one after another, without any intervening comments or blank lines.
"""

        # Prioritize patch failure feedback if present, otherwise use reviewer suggestions
        if feedback_context:
            # This is a retry after a patch application failure
            file_contexts = feedback_context.get('file_contexts', [])
            
            file_context_str = ""
            if file_contexts:
                file_context_str += "**Context for files relevant to this failed patch:**\n"
                for file_info in file_contexts:
                    file_context_str += f"- File: `{file_info['filename']}`\n"
                    if file_info['exists']:
                        file_context_str += f"  - Status: EXISTS, {file_info['num_lines']} lines\n"
                        file_context_str += "  --- START FILE CONTENT ---\n"
                        file_context_str += f"{file_info['content']}\n"
                        file_context_str += "  --- END FILE CONTENT ---\n"
                    else:
                        file_context_str += "  - Status: DOES NOT EXIST (You should create it with the correct diff format)\n"
            else:
                file_context_str = "Could not automatically determine files relevant to this patch failure."

            return f"""You are an expert software engineer specializing in fixing diff application errors.
Your previous attempt to generate a diff for the following task failed to apply to the codebase.

**Original Task:** {task['description']}

**Acceptance Criteria:**
{chr(10).join([f"- {c}" for c in task['acceptance_criteria']])}

**Error Message from the `patch` command:**
{feedback_context['patch_error']}

{file_context_str}

**Your Previously Generated Broken Diff:**
```diff
{feedback_context['broken_diff']}
```
{diff_formatting_instructions}
**Instructions:**
Analyze the error message, the actual file content (if provided), and the original task. The `patch` error, combined with the file's current state, should tell you exactly what is wrong.

Generate a **new, corrected unified diff** that fixes the problem.
- If the file exists, ensure your diff's context lines (`-`, `+`, ` `) EXACTLY match the provided file content.
- If the file does not exist, ensure you are using the correct "new file" diff format.
Include only the minimal necessary changes.
"""
        elif suggestions:
            # This is a retry after general validation failure with reviewer suggestions
            return f"""You are an expert software engineer. Your previous implementation for the following task failed validation.

**Original Task:** {task['description']}

**Acceptance Criteria:**
{chr(10).join([f"- {c}" for c in task['acceptance_criteria']])}

**Reviewer Suggestions for Improvement:**
{chr(10).join([f"- {s}" for s in suggestions])}
{diff_formatting_instructions}
**Instructions:**
Based on the reviewer's feedback, provide a new unified diff to correct the implementation.
Include only the minimal necessary changes to address the suggestions.
"""
        else:
            # This is the first attempt
            return f"""You are an expert software engineer. Implement this task.

Task: {task['description']}

Acceptance Criteria:
{chr(10).join([f"- {c}" for c in task['acceptance_criteria']])}

Context:
{task.get('context', 'No additional context')}
{diff_formatting_instructions}
Provide a unified diff that implements this task.
Include only the minimal necessary changes."""
    
    def _build_reviewer_prompt(self, validation_result: Dict) -> str:
        """Build prompt for Reviewer agent"""
        failures = validation_result.get('failures', [])
        
        return f"""You are an expert code reviewer. Analyze these test failures and suggest fixes.

Test Failures:
{chr(10).join([f"- {f}" for f in failures])}

Coverage: {validation_result.get('coverage', 'N/A')}%

Suggest specific corrective actions or recommend rollback."""
    
    def _build_refiner_prompt(self) -> str:
        """Build prompt for Refiner agent"""
        return """You are an expert in code refactoring. Improve the code structure without changing behavior.

Focus on:
- Naming clarity
- Function decomposition
- Code organization

Provide a unified diff with refactoring changes."""
    
    def _parse_task_graph(self, response: Dict) -> Dict:
        """Parse task graph from agent response"""
        text = response.get('text', '')
        
        try:
            # Remove markdown code blocks if present
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            return json.loads(text.strip())
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse task graph: {e}")
            logger.debug("Full response text was:\n%s", text)
            # Return minimal valid structure
            return {'tasks': []}
    
    def _parse_tests(self, response: Dict) -> Dict:
        """Parse test definitions from agent response"""
        return {
            'test_code': response.get('text', ''),
            'test_count': response.get('metadata', {}).get('test_count', 0)
        }
