# git_repo_analyzer/cli.py
import click
import os
from git_repo_analyzer.analyzer import analyze_repository

@click.group()
def cli():
    """Git Repository Analyzer CLI"""
    pass

# --- New "scan" command (preferred) ---
@cli.command()
@click.argument("path", required=False)
@click.option("--report", "-r", type=click.Choice(["html", "md"]), help="Generate report in specified format")
@click.option("--show-branches", is_flag=True, help="Include branch statistics")
@click.option("--complexity", is_flag=True, help="Include code complexity analysis")
def scan(path, report, show_branches, complexity):
    """Scan a repository (preferred command)"""
    if not path:
        click.echo("Please specify a repository path.")
        return

    repo_source = ("local", path)
    analyze_repository(repo_source, report, show_branches, complexity)


# --- Legacy "analyze" command (kept for .exe compatibility) ---
@cli.command()
@click.argument("path", required=False)
@click.option("--url", "-u", help="GitHub repository URL to clone and analyze.")
@click.option("--local", "-l", type=click.Path(exists=True), help="Local repository path to analyze.")
@click.option("--report", "-r", type=click.Choice(["html", "md"]), help="Generate report in specified format")
@click.option("--show-branches", is_flag=True, help="Include branch statistics")
@click.option("--complexity", is_flag=True, help="Include code complexity analysis")
def analyze(path, url, local, report, show_branches, complexity):
    """Analyze a repository (legacy command)"""
    if local:
        repo_source = ("local", local)
    elif url:
        repo_source = ("url", url)
    elif path:
        repo_source = ("local", path)
    else:
        click.echo("Provide either a local path or a --url to clone.")
        return

    analyze_repository(repo_source, report, show_branches, complexity)
    


if __name__ == "__main__":
    cli()
