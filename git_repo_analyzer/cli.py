import click
from git_repo_analyzer.analyzer import analyze_repository


@click.group()
def cli():
    """Git Repository Analyzer CLI"""
    pass


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
def analyze(repo_path):
    """Analyze a local Git repository."""
    analyze_repository(repo_path)


if __name__ == "__main__":
    cli()
