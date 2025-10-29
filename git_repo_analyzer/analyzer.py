from git import Repo
from collections import Counter
from rich.console import Console

console = Console()


def analyze_repository(repo_path: str):
    """Analyze a Git repository and print basic statistics."""
    try:
        repo = Repo(repo_path)
    except Exception as e:
        console.print(f"[red]Error loading repo:[/red] {e}")
        return

    if repo.bare:
        console.print("[red]This repository is empty or bare.[/red]")
        return

    # Gather basic stats
    commits = list(repo.iter_commits())
    authors = [commit.author.name for commit in commits if commit.author]

    author_counts = Counter(authors)

    console.print(f"\n[bold blue]📊 Repository Analysis[/bold blue]")
    console.print(f"[green]Path:[/green] {repo_path}")
    console.print(f"[green]Total commits:[/green] {len(commits)}")
    console.print(f"[green]Unique authors:[/green] {len(author_counts)}\n")

    console.print("[bold]Commits per Author:[/bold]")
    for author, count in author_counts.items():
        console.print(f"  - {author}: {count} commits")

    console.print("\n✅ [bold green]Analysis complete![/bold green]\n")
