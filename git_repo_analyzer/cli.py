# git_repo_analyzer/cli.py
import click
from git_repo_analyzer.analyzer import analyze_repository
import os

@click.group()
def cli():
    """Git Repository Analyzer CLI"""
    pass

@cli.command()
@click.argument("path", required=False)
@click.option("--url", "-u", help="GitHub repository URL to clone and analyze (e.g. https://github.com/user/repo).")
@click.option("--local", "-l", type=click.Path(exists=True), help="Local repository path to analyze.")
def analyze(path, url, local):
    """
    Analyze a repository.

    Usage examples:
      repo-analyzer /path/to/local/repo
      repo-analyzer --local /path/to/local/repo
      repo-analyzer --url https://github.com/user/repo
    """
    repo_source = None

    # Priority: explicit --local, then explicit --url, then positional path (local).
    if local:
        repo_source = ("local", local)
    elif url:
        repo_source = ("url", url)
    elif path:
        # treat positional argument as a path (local)
        repo_source = ("local", path)
    else:
        click.echo("Provide either a local path or a --url to clone. See --help for usage.")
        return

    analyze_repository(repo_source)

if __name__ == "__main__":
    cli()
