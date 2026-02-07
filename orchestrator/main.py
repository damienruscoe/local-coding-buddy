"""
Main orchestrator entry point for the Local AI Coding Buddy.
"""
import os
import sys
import click
import logging
from pathlib import Path

from .state_machine import StateMachine
from .config_loader import ConfigLoader
from .logger import setup_logging


@click.group()
def cli():
    """Local AI Coding Buddy - Autonomous coding assistant"""
    pass


@cli.command()
@click.option('--project', type=str, required=True,
              help='Path to project directory')
@click.option('--request', type=str, required=True,
              help='Coding request description')
@click.option('--auto-commit/--no-auto-commit', default=False,
              help='Automatically commit successful changes')
def run(project: str, request: str, auto_commit: bool):
    """Execute a coding request"""
    setup_logging('DEBUG')
    logging.info("RUN INVOKED")
    logging.info("Project arg: %s", project)
    logging.info("CWD: %s", os.getcwd())
    try:
        logging.info("Listing /workspace: %s", os.listdir("/workspace"))
    except FileNotFoundError:
        logging.warning("/workspace not found, skipping listing.")

    try:
        config = ConfigLoader.load()
        
        logging.info("[bold blue]Starting coding buddy...[/bold blue]")
        logging.info(f"Project: {project}")
        logging.info(f"Request: {request}")
        
        state_machine = StateMachine(
            project_path=Path(project),
            config=config,
            auto_commit=auto_commit
        )
        
        result = state_machine.execute(request)
        
        if result.success:
            logging.info("[bold green]✓ Task completed successfully![/bold green]")
            if result.commit_hash:
                logging.info(f"Commit: {result.commit_hash}")
        else:
            logging.error("[bold red]✗ Task failed: {result.error}[/bold red]")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"[bold red]Error: {e}[/bold red]", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--project', type=click.Path(exists=True), required=True)
def scan(project: str):
    """Scan existing codebase and generate summaries"""
    from .scanner import CodebaseScanner
    
    setup_logging()
    logging.info("[bold blue]Scanning codebase...[/bold blue]")
    scanner = CodebaseScanner(Path(project))
    summary = scanner.scan()
    
    logging.info("[bold green]Scan complete![/bold green]")
    logging.info(f"Files: {summary['file_count']}")
    logging.info(f"Modules: {len(summary['modules'])}")
    logging.info(f"Build targets: {len(summary['build_targets'])}")


@cli.command()
def status():
    """Show current system status"""
    from .state_machine import StateMachine
    
    setup_logging()
    state = StateMachine.load_state()
    if state:
        logging.info(f"[bold]Current state:[/bold] {state.current_state}")
        logging.info(f"Task: {state.current_task}")
        logging.info(f"Retry count: {state.retry_count}")
    else:
        logging.info("No active task")


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()
