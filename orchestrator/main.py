"""
Main orchestrator entry point for the Local AI Coding Buddy.
"""
import sys
import click
from rich.console import Console
from pathlib import Path

from .state_machine import StateMachine
from .config_loader import ConfigLoader
from .logger import setup_logging

console = Console()


@click.group()
def cli():
    """Local AI Coding Buddy - Autonomous coding assistant"""
    pass


@cli.command()
@click.option('--project', type=click.Path(exists=True), required=True,
              help='Path to project directory')
@click.option('--request', type=str, required=True,
              help='Coding request description')
@click.option('--auto-commit/--no-auto-commit', default=False,
              help='Automatically commit successful changes')
def run(project: str, request: str, auto_commit: bool):
    """Execute a coding request"""
    try:
        setup_logging()
        config = ConfigLoader.load()
        
        console.print(f"[bold blue]Starting coding buddy...[/bold blue]")
        console.print(f"Project: {project}")
        console.print(f"Request: {request}")
        
        state_machine = StateMachine(
            project_path=Path(project),
            config=config,
            auto_commit=auto_commit
        )
        
        result = state_machine.execute(request)
        
        if result.success:
            console.print(f"[bold green]✓ Task completed successfully![/bold green]")
            if result.commit_hash:
                console.print(f"Commit: {result.commit_hash}")
        else:
            console.print(f"[bold red]✗ Task failed: {result.error}[/bold red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise
        sys.exit(1)


@cli.command()
@click.option('--project', type=click.Path(exists=True), required=True)
def scan(project: str):
    """Scan existing codebase and generate summaries"""
    from .scanner import CodebaseScanner
    
    console.print(f"[bold blue]Scanning codebase...[/bold blue]")
    scanner = CodebaseScanner(Path(project))
    summary = scanner.scan()
    
    console.print(f"[bold green]Scan complete![/bold green]")
    console.print(f"Files: {summary['file_count']}")
    console.print(f"Modules: {len(summary['modules'])}")
    console.print(f"Build targets: {len(summary['build_targets'])}")


@cli.command()
def status():
    """Show current system status"""
    from .state_machine import StateMachine
    
    state = StateMachine.load_state()
    if state:
        console.print(f"[bold]Current state:[/bold] {state.current_state}")
        console.print(f"Task: {state.current_task}")
        console.print(f"Retry count: {state.retry_count}")
    else:
        console.print("No active task")


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()
