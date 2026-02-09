#!/usr/bin/env python3
"""
Standalone Example: Using the Enhanced Implementer Workflow

This shows how to use the new implementer workflow without needing
the full orchestrator infrastructure.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.context_extractor import extract_context
from orchestrator.v4a_patch import V4APatchApplier


class MockAgentsClient:
    """
    Mock agents client for demonstration.
    
    In real usage, this would call your actual LLM (llama.cpp, OpenAI, etc.)
    """
    
    def call_agent(self, agent_type: str, input_data: dict) -> str:
        """
        Simulate calling an LLM agent.
        
        In reality, you would:
        1. Build a prompt from input_data
        2. Call your LLM
        3. Return the response
        """
        print(f"\n{'='*80}")
        print(f"CALLING {agent_type.upper()} AGENT")
        print(f"{'='*80}")
        
        # Show what context the agent receives
        if 'file_context' in input_data:
            ctx = input_data['file_context']
            print(f"\nFile: {ctx['file_path']}")
            print(f"Exists: {ctx['file_exists']}")
            print(f"Action: {ctx['action']}")
            print(f"Strategy: {ctx.get('strategy', 'unknown')}")
            
            if ctx.get('all_symbols'):
                print(f"\nAvailable symbols: {ctx['all_symbols']}")
            
            if ctx.get('relevant_sections'):
                print(f"\nRelevant sections: {len(ctx['relevant_sections'])}")
                for i, section in enumerate(ctx['relevant_sections'][:2], 1):
                    print(f"\n  Section {i}:")
                    if section.get('symbol'):
                        print(f"    Symbol: {section['symbol']}")
                    print(f"    Lines: {section['line_start']}-{section['line_end']}")
                    print(f"    Preview: {section['lines'][:100]}...")
        
        print(f"\nTask: {input_data['task']['description']}")
        
        # In real usage, this is where you'd call your LLM
        # For this demo, we'll return a hardcoded V4A patch
        
        if input_data['file_context']['file_exists']:
            # Update existing file
            patch = f'''*** Begin Patch
*** Update File: {input_data['file_context']['file_path']}
@@ def greet @@
 def greet(name):
-    return "Hello"
+    return f"Hello, {{name}}!"
*** End Patch
'''
        else:
            # Create new file
            patch = f'''*** Begin Patch
*** Add File: {input_data['file_context']['file_path']}
+def fibonacci(n):
+    """Calculate nth Fibonacci number."""
+    if n <= 1:
+        return n
+    return fibonacci(n-1) + fibonacci(n-2)
*** End Patch
'''
        
        print(f"\n{'='*80}")
        print("AGENT RESPONSE (V4A PATCH):")
        print(f"{'='*80}")
        print(patch)
        
        return patch


def example_1_update_existing_file():
    """Example 1: Update an existing file."""
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Update Existing File")
    print("="*80)
    
    # Create a test file
    test_file = 'example_greet.py'
    with open(test_file, 'w') as f:
        f.write('''def greet(name):
    return "Hello"

def farewell(name):
    return "Goodbye"
''')
    
    print(f"\nCreated test file: {test_file}")
    print("\nOriginal content:")
    with open(test_file, 'r') as f:
        print(f.read())
    
    # Step 1: Extract context
    print("\n" + "-"*80)
    print("STEP 1: Extract Context")
    print("-"*80)
    
    task_description = "Update the greet function to use f-strings"
    context = extract_context(
        file_path=test_file,
        task_description=task_description,
        strategy="ast"  # Change this to try different strategies!
    )
    
    print(f"\nContext extraction strategy: {context.strategy}")
    print(f"Found symbols: {context.all_symbols}")
    print(f"Relevant sections: {len(context.relevant_sections)}")
    
    # Step 2: Call agent with context
    print("\n" + "-"*80)
    print("STEP 2: Call Implementer Agent")
    print("-"*80)
    
    agents_client = MockAgentsClient()
    
    task = {
        'description': task_description,
        'acceptance_criteria': ['Use f-strings', 'Include name parameter']
    }
    
    implementer_input = {
        'task': task,
        'file_context': context.to_dict(),
        'output_format': 'v4a_patch',
        'instructions': 'Use V4A format...'
    }
    
    patch = agents_client.call_agent('implementer', implementer_input)
    
    # Step 3: Apply patch
    print("\n" + "-"*80)
    print("STEP 3: Apply V4A Patch")
    print("-"*80)
    
    applier = V4APatchApplier(verbose=True)
    result = applier.apply_patch(patch)
    
    print(f"\nPatch application result:")
    print(f"  Success: {result['success']}")
    
    if result['success']:
        for op in result['operations']:
            print(f"  Operation: {op.action}")
            print(f"  Match strategy: {op.match_strategy}")
            print(f"  Line range: {op.line_range}")
        
        print("\n" + "-"*80)
        print("UPDATED FILE CONTENT:")
        print("-"*80)
        with open(test_file, 'r') as f:
            print(f.read())
    else:
        print(f"  Errors: {result['errors']}")
    
    # Cleanup
    os.remove(test_file)
    print("\nCleaned up test file.")


def example_2_create_new_file():
    """Example 2: Create a new file."""
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Create New File")
    print("="*80)
    
    test_file = 'new_fibonacci.py'
    
    # Step 1: Extract context (file doesn't exist)
    print("\n" + "-"*80)
    print("STEP 1: Extract Context")
    print("-"*80)
    
    context = extract_context(
        file_path=test_file,
        task_description="Create a Fibonacci function",
        strategy="ast"
    )
    
    print(f"\nFile exists: {context.file_exists}")
    print(f"Action: {context.action}")
    
    # Step 2: Call agent
    print("\n" + "-"*80)
    print("STEP 2: Call Implementer Agent")
    print("-"*80)
    
    agents_client = MockAgentsClient()
    
    task = {
        'description': 'Create a Fibonacci function',
        'acceptance_criteria': ['Recursive implementation', 'Handle base cases']
    }
    
    implementer_input = {
        'task': task,
        'file_context': context.to_dict(),
        'output_format': 'v4a_patch',
        'instructions': 'Use V4A format...'
    }
    
    patch = agents_client.call_agent('implementer', implementer_input)
    
    # Step 3: Apply patch
    print("\n" + "-"*80)
    print("STEP 3: Apply V4A Patch")
    print("-"*80)
    
    applier = V4APatchApplier(verbose=True)
    result = applier.apply_patch(patch)
    
    print(f"\nPatch application result:")
    print(f"  Success: {result['success']}")
    
    if result['success']:
        print("\n" + "-"*80)
        print("NEW FILE CONTENT:")
        print("-"*80)
        with open(test_file, 'r') as f:
            print(f.read())
        
        # Cleanup
        os.remove(test_file)
        print("\nCleaned up test file.")
    else:
        print(f"  Errors: {result['errors']}")


def example_3_using_workflow_helper():
    """Example 3: Using the workflow helper function."""
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Using Workflow Helper")
    print("="*80)
    
    from orchestrator.implementer_workflow import ImplementerStage
    
    # Create test file
    test_file = 'workflow_test.py'
    with open(test_file, 'w') as f:
        f.write('''def add(a, b):
    return a + b
''')
    
    print(f"\nCreated test file: {test_file}")
    
    # Use the ImplementerStage directly
    print("\n" + "-"*80)
    print("Using ImplementerStage")
    print("-"*80)
    
    stage = ImplementerStage(config_path="../config/config.yaml")
    agents_client = MockAgentsClient()
    
    task = {
        'description': 'Add docstring to add function',
        'acceptance_criteria': ['Include parameter descriptions']
    }
    
    result = stage.run_implementer(task, test_file, agents_client)
    
    print(f"\nWorkflow result:")
    print(f"  Success: {result['success']}")
    print(f"  Attempt: {result.get('attempt', 'N/A')}")
    print(f"  Strategy: {result.get('context_strategy', 'N/A')}")
    
    # Cleanup
    os.remove(test_file)
    print("\nCleaned up test file.")


def show_integration_pattern():
    """Show how this integrates into your orchestrator."""
    
    print("\n" + "="*80)
    print("INTEGRATION PATTERN")
    print("="*80)
    
    print("""
To integrate into your existing orchestrator:

1. FIND your current implementer call:

    # Old way (somewhere in your orchestrator code):
    implementer_input = {
        'task': task,
        'file_path': file_path
    }
    patch_text = agents_client.call_agent('implementer', implementer_input)
    
    # Apply patch (brittle!)
    os.system('patch -p1 < temp.patch')


2. REPLACE with new workflow:

    from orchestrator.implementer_workflow import run_implementer_stage
    
    result = run_implementer_stage(
        task=task,
        file_path=file_path,
        agents_client=agents_client  # Your existing client
    )
    
    if result['success']:
        print(f"Implemented using {result['context_strategy']} strategy")
        print(f"Took {result['attempt']} attempt(s)")
    else:
        print(f"Failed: {result['last_error']}")


3. UPDATE your agents_client.call_agent() method:

    def call_agent(self, agent_type: str, input_data: dict) -> str:
        # Build prompt including the new fields:
        # - input_data['file_context'] (rich context)
        # - input_data['instructions'] (V4A format)
        # - input_data['previous_attempt'] (if retry)
        # - input_data['suggestions'] (if retry)
        
        prompt = build_prompt(agent_type, input_data)
        response = call_llm(prompt)
        return response


That's it! The workflow handles:
- Context extraction
- V4A patch validation
- Retry with feedback
- Robust application
""")


if __name__ == "__main__":
    print("="*80)
    print("ENHANCED IMPLEMENTER WORKFLOW - STANDALONE EXAMPLES")
    print("="*80)
    print("\nThese examples show how to use the new workflow components")
    print("without needing the full orchestrator setup.")
    print()
    
    # Change directory to a temp location
    os.chdir('/tmp')
    
    example_1_update_existing_file()
    example_2_create_new_file()
    
    # Note: Example 3 requires config file, so we'll skip it in standalone mode
    # example_3_using_workflow_helper()
    
    show_integration_pattern()
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Review how context extraction works")
    print("2. See how V4A patches are applied")
    print("3. Integrate into your orchestrator using the pattern above")
