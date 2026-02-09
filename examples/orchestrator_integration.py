"""
Mock Orchestrator Integration Example

This shows a complete orchestrator integration using the new enhanced
implementer workflow. This is a working example you can adapt to your
existing orchestrator.
"""

import os
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import the new enhanced components
from orchestrator.implementer_workflow import run_implementer_stage
from orchestrator.v4a_patch import V4APatchApplier


@dataclass
class Task:
    """Represents a coding task."""
    description: str
    file_path: str
    acceptance_criteria: List[str]
    tests: Optional[List[str]] = None


class MockAgentsClient:
    """
    Mock implementation of agents client.
    
    REPLACE THIS with your actual LLM integration.
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        print(f"[AgentsClient] Initialized with model: {model_path}")
    
    def call_agent(self, agent_type: str, input_data: Dict) -> str:
        """
        Call an LLM agent.
        
        YOUR IMPLEMENTATION should:
        1. Build a prompt from input_data
        2. Call your LLM (llama.cpp, OpenAI API, etc.)
        3. Return the LLM's response
        """
        
        if agent_type == 'architect':
            return self._mock_architect(input_data)
        elif agent_type == 'spec_author':
            return self._mock_spec_author(input_data)
        elif agent_type == 'implementer':
            return self._mock_implementer(input_data)
        elif agent_type == 'reviewer':
            return self._mock_reviewer(input_data)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def _mock_implementer(self, input_data: Dict) -> str:
        """
        Mock implementer response.
        
        In reality, you would:
        1. Build prompt with file_context, task, V4A instructions
        2. Call LLM
        3. Return V4A formatted patch
        """
        
        file_path = input_data['file_context']['file_path']
        file_exists = input_data['file_context']['file_exists']
        
        if file_exists:
            # Generate update patch
            patch = f'''*** Begin Patch
*** Update File: {file_path}
@@ def example @@
 def example():
-    return "old"
+    """Updated function."""
+    return "new"
*** End Patch
'''
        else:
            # Generate add patch
            patch = f'''*** Begin Patch
*** Add File: {file_path}
+def hello():
+    """A greeting function."""
+    return "Hello, World!"
+
+def fibonacci(n):
+    """Calculate Fibonacci number."""
+    if n <= 1:
+        return n
+    return fibonacci(n-1) + fibonacci(n-2)
*** End Patch
'''
        
        return patch
    
    def _mock_architect(self, input_data: Dict) -> str:
        """Mock architect - returns task decomposition."""
        return "tasks"  # Simplified
    
    def _mock_spec_author(self, input_data: Dict) -> str:
        """Mock spec author - returns test specs."""
        return "test specs"  # Simplified
    
    def _mock_reviewer(self, input_data: Dict) -> str:
        """Mock reviewer - returns code review."""
        return "review"  # Simplified


class EnhancedOrchestrator:
    """
    Example orchestrator integrating the enhanced implementer workflow.
    
    This shows how to integrate into your existing orchestrator.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize orchestrator."""
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize agents client
        self.agents_client = MockAgentsClient(
            model_path=self.config.get('model_path')
        )
        
        self.config_path = config_path
        
        print(f"[Orchestrator] Initialized")
        print(f"[Orchestrator] Context strategy: {self.config['context_extraction_strategy']}")
    
    def process_request(self, request: str, project_path: str) -> Dict:
        """
        Process a user coding request.
        
        This is your main workflow entry point.
        """
        
        print(f"\n{'='*80}")
        print(f"PROCESSING REQUEST: {request}")
        print(f"{'='*80}\n")
        
        # Stage 1: Architect - decompose request into tasks
        tasks = self._architect_stage(request, project_path)
        print(f"[Architect] Generated {len(tasks)} task(s)")
        
        # Stage 2: Spec Author - generate tests for each task
        for task in tasks:
            task.tests = self._spec_author_stage(task)
            print(f"[Spec Author] Generated tests for: {task.description}")
        
        # Stage 3: Implementer - write code (ENHANCED!)
        results = []
        for i, task in enumerate(tasks, 1):
            print(f"\n{'='*80}")
            print(f"IMPLEMENTING TASK {i}/{len(tasks)}: {task.description}")
            print(f"{'='*80}\n")
            
            # THIS IS THE KEY INTEGRATION POINT
            # Replace your old implementer call with this:
            impl_result = run_implementer_stage(
                task={
                    'description': task.description,
                    'acceptance_criteria': task.acceptance_criteria
                },
                file_path=task.file_path,
                agents_client=self.agents_client,
                config_path=self.config_path
            )
            
            print(f"\n[Implementer] Result:")
            print(f"  Success: {impl_result['success']}")
            if impl_result['success']:
                print(f"  Attempts: {impl_result['attempt']}")
                print(f"  Strategy: {impl_result['context_strategy']}")
            else:
                print(f"  Error: {impl_result.get('last_error')}")
            
            # Stage 4: Run tests (your existing test runner)
            if impl_result['success']:
                test_result = self._run_tests(task)
                print(f"[Tests] Passed: {test_result['passed']}")
                
                if not test_result['passed']:
                    # Stage 5: Reviewer (your existing reviewer)
                    review = self._reviewer_stage(task, test_result)
                    print(f"[Reviewer] Feedback: {review}")
                    
                    # Could retry implementer here with review feedback
                
                results.append({
                    'task': task,
                    'implementation': impl_result,
                    'tests': test_result
                })
            else:
                results.append({
                    'task': task,
                    'implementation': impl_result,
                    'error': 'Implementation failed'
                })
        
        # Summary
        success = all(r.get('tests', {}).get('passed', False) for r in results)
        
        print(f"\n{'='*80}")
        print(f"WORKFLOW COMPLETE")
        print(f"{'='*80}")
        print(f"Success: {success}")
        print(f"Tasks completed: {len([r for r in results if r.get('tests', {}).get('passed')])}/{len(results)}")
        
        return {
            'success': success,
            'results': results
        }
    
    def _architect_stage(self, request: str, project_path: str) -> List[Task]:
        """
        Stage 1: Decompose request into tasks.
        
        YOUR IMPLEMENTATION: Call your actual architect agent.
        """
        
        # Mock implementation - replace with your architect call
        return [
            Task(
                description="Add a fibonacci function",
                file_path=os.path.join(project_path, "math_utils.py"),
                acceptance_criteria=[
                    "Implement recursive fibonacci",
                    "Handle base cases n=0 and n=1",
                    "Include docstring"
                ]
            )
        ]
    
    def _spec_author_stage(self, task: Task) -> List[str]:
        """
        Stage 2: Generate test specifications.
        
        YOUR IMPLEMENTATION: Call your actual spec author agent.
        """
        
        # Mock implementation - replace with your spec author call
        return [
            "test_fibonacci_base_case_0",
            "test_fibonacci_base_case_1",
            "test_fibonacci_recursive"
        ]
    
    def _run_tests(self, task: Task) -> Dict:
        """
        Stage 4: Run tests.
        
        YOUR IMPLEMENTATION: Call your actual test runner.
        """
        
        # Mock implementation - replace with your test runner
        return {
            'passed': True,
            'failures': [],
            'coverage': 95.0
        }
    
    def _reviewer_stage(self, task: Task, test_result: Dict) -> str:
        """
        Stage 5: Review failed implementation.
        
        YOUR IMPLEMENTATION: Call your actual reviewer agent.
        """
        
        # Mock implementation - replace with your reviewer call
        return "Code looks good but tests failed on edge case"


def demo_integration():
    """Demonstrate the complete integration."""
    
    print("="*80)
    print("ENHANCED ORCHESTRATOR INTEGRATION DEMO")
    print("="*80)
    print()
    print("This demonstrates how the new implementer workflow")
    print("integrates into your existing orchestrator.")
    print()
    
    # Create a temporary project directory
    project_path = "/tmp/demo_project"
    os.makedirs(project_path, exist_ok=True)
    
    # Create test file that will be updated
    test_file = os.path.join(project_path, "math_utils.py")
    with open(test_file, 'w') as f:
        f.write("""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")
    
    print(f"Created demo project at: {project_path}")
    print(f"Created initial file: math_utils.py\n")
    
    # Initialize orchestrator
    # Note: Using default config path - adjust as needed
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "config",
        "config.yaml"
    )
    
    orchestrator = EnhancedOrchestrator(config_path=config_path)
    
    # Process a request
    result = orchestrator.process_request(
        request="Add a fibonacci function to math_utils.py",
        project_path=project_path
    )
    
    print(f"\n{'='*80}")
    print("FINAL RESULT")
    print(f"{'='*80}")
    print(f"Overall success: {result['success']}")
    print(f"\nTasks:")
    for i, r in enumerate(result['results'], 1):
        task = r['task']
        impl = r['implementation']
        print(f"\n{i}. {task.description}")
        print(f"   File: {task.file_path}")
        print(f"   Success: {impl['success']}")
        if impl['success']:
            print(f"   Strategy: {impl['context_strategy']}")
            print(f"   Attempts: {impl['attempt']}")
        
        if os.path.exists(task.file_path):
            print(f"\n   Final file content:")
            with open(task.file_path, 'r') as f:
                for line in f:
                    print(f"   | {line}", end='')
    
    # Cleanup
    import shutil
    shutil.rmtree(project_path)
    print(f"\n\nCleaned up demo project.")


def show_migration_path():
    """Show how to migrate from old to new approach."""
    
    print("\n" + "="*80)
    print("MIGRATION PATH: OLD → NEW")
    print("="*80)
    
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ OLD APPROACH (In your current orchestrator)                     │
└─────────────────────────────────────────────────────────────────┘

def execute_implementer(self, task, file_path):
    # 1. Minimal context
    implementer_input = {
        'task': task,
        'file_path': file_path
    }
    
    # 2. Call LLM
    patch_text = self.agents_client.call_agent(
        'implementer',
        implementer_input
    )
    
    # 3. Apply patch (brittle!)
    with open('temp.patch', 'w') as f:
        f.write(patch_text)
    
    os.system('patch -p1 < temp.patch')  # Often fails!
    
    # No retry, no validation, no error feedback


┌─────────────────────────────────────────────────────────────────┐
│ NEW APPROACH (Using enhanced workflow)                          │
└─────────────────────────────────────────────────────────────────┘

from orchestrator.implementer_workflow import run_implementer_stage

def execute_implementer(self, task, file_path):
    # Everything handled automatically:
    # - Context extraction (with chosen strategy)
    # - V4A patch generation
    # - Validation
    # - Robust application
    # - Retry with feedback
    
    result = run_implementer_stage(
        task=task,
        file_path=file_path,
        agents_client=self.agents_client,  # Same client!
        config_path=self.config_path
    )
    
    if result['success']:
        print(f"Success! Used {result['context_strategy']} strategy")
        print(f"Took {result['attempt']} attempt(s)")
        return result
    else:
        print(f"Failed: {result['last_error']}")
        # Could implement fallback here
        return result


┌─────────────────────────────────────────────────────────────────┐
│ WHAT TO UPDATE IN YOUR AGENTS CLIENT                            │
└─────────────────────────────────────────────────────────────────┘

The new workflow passes richer input_data to your agents_client.
You need to update your prompt building to use these fields:

def call_agent(self, agent_type, input_data):
    if agent_type == 'implementer':
        # OLD: Only had task and file_path
        # NEW: Now includes:
        # - input_data['file_context']     ← Rich context
        # - input_data['instructions']     ← V4A format rules
        # - input_data['previous_attempt'] ← If retry
        # - input_data['errors']           ← Why it failed
        # - input_data['suggestions']      ← Similar code hints
        
        prompt = self._build_implementer_prompt(input_data)
    
    response = self._call_llm(prompt)
    return response


┌─────────────────────────────────────────────────────────────────┐
│ THAT'S IT!                                                       │
└─────────────────────────────────────────────────────────────────┘

Three changes:
1. Import run_implementer_stage
2. Replace your implementer call with it
3. Update prompt building to use new context fields

Everything else (architect, spec_author, reviewer) stays the same!
""")


if __name__ == "__main__":
    demo_integration()
    show_migration_path()
    
    print("\n" + "="*80)
    print("INTEGRATION DEMO COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the EnhancedOrchestrator class above")
    print("2. Compare with your current orchestrator")
    print("3. Follow the migration path to integrate")
    print("4. Test with your actual LLM and codebase")
