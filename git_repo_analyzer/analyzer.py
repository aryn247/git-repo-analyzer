# git_repo_analyzer/analyzer.py
import os
import shutil
from collections import Counter
from datetime import datetime
from rich.console import Console
import matplotlib.pyplot as plt
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
from git import Repo, GitCommandError
from typing import Tuple, Dict, Optional

console = Console()

def is_git_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://") or s.endswith(".git")

def clone_repo_from_url(url: str) -> str:
    """
    Clone the repo into ./cloned_repos/<repo-name>_<timestamp> and return the path.
    If path exists, add a timestamp suffix.
    """
    base_dir = os.path.abspath("cloned_repos")
    os.makedirs(base_dir, exist_ok=True)

    repo_name = url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = os.path.join(base_dir, f"{repo_name}_{timestamp}")

    try:
        console.print(f"[yellow]Cloning {url} → {dest}[/yellow]")
        Repo.clone_from(url, dest)
    except GitCommandError as e:
        console.print(f"[red]Failed to clone repository:[/red] {e}")
        raise

    return dest

def get_language_usage(repo_path: str) -> Dict[str, int]:
    """Scan repo files and return language usage (bytes per language)."""
    language_sizes: Dict[str, int] = {}
    for root, dirs, files in os.walk(repo_path):
        if ".git" in dirs:
            dirs.remove(".git")  # skip git internals
        for f in files:
            path = os.path.join(root, f)
            # ignore binary files that are huge (just try/except)
            try:
                with open(path, encoding="utf-8", errors="ignore") as file:
                    content = file.read(8192)  # read a chunk for detection
                try:
                    lexer = guess_lexer_for_filename(f, content)
                    lang = lexer.name
                except ClassNotFound:
                    continue
                size = os.path.getsize(path)
                language_sizes[lang] = language_sizes.get(lang, 0) + size
            except (UnicodeDecodeError, OSError):
                continue
    return language_sizes

def analyze_repository(repo_source: Tuple[str, str] or str):
    """
    repo_source may be:
      - ("local", "/path/to/repo")
      - ("url", "https://github.com/user/repo")
      - or simply a string path (legacy)
    """
    # Normalize input
    if isinstance(repo_source, tuple):
        mode, value = repo_source
    else:
        # if string provided, treat as local path
        if is_git_url(repo_source):
            mode, value = ("url", repo_source)
        else:
            mode, value = ("local", repo_source)

    repo_path = None
    cloned_for_cleanup = False

    try:
        if mode == "url":
            repo_path = clone_repo_from_url(value)
            cloned_for_cleanup = False  # keep cloned copy by default
        else:
            repo_path = os.path.abspath(value)

        # load repo
        try:
            repo = Repo(repo_path)
        except Exception as e:
            console.print(f"[red]Error loading repo at {repo_path}:[/red] {e}")
            return

        if repo.bare:
            console.print("[red]This repository is empty or bare.[/red]")
            return

        # Gather commits
        commits = list(repo.iter_commits())
        if not commits:
            console.print("[yellow]No commits found in this repository.[/yellow]")
            return

        authors = [commit.author.name if commit.author and commit.author.name else "Unknown" for commit in commits]
        author_counts = Counter(authors)

        # --- PRINT BASIC STATS ---
        console.print(f"\n[bold blue]📊 Repository Analysis[/bold blue]")
        console.print(f"[green]Path:[/green] {repo_path}")
        console.print(f"[green]Total commits:[/green] {len(commits)}")
        console.print(f"[green]Unique authors:[/green] {len(author_counts)}\n")

        console.print("[bold]Commits per Author:[/bold]")
        for author, count in author_counts.most_common():
            console.print(f"  - {author}: {count} commits")

        # --- COMMIT FREQUENCY CHART ---
        commit_dates = [datetime.fromtimestamp(commit.committed_date) for commit in commits]
        monthly_counts = Counter([d.strftime("%Y-%m") for d in commit_dates])
        sorted_months = sorted(monthly_counts.keys())
        counts = [monthly_counts[m] for m in sorted_months]

        # --- LANGUAGE USAGE ---
        language_sizes = get_language_usage(repo_path)
        language_chart_path: Optional[str] = None
        if language_sizes:
            labels = list(language_sizes.keys())
            sizes = list(language_sizes.values())

            plt.figure(figsize=(6,6))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            plt.title("Language Usage in Repo")
            os.makedirs("reports", exist_ok=True)
            language_chart_path = os.path.join("reports", "language_usage.png")
            plt.savefig(language_chart_path)
            plt.close()
            console.print(f"🖼️ Language usage chart saved to: [cyan]{language_chart_path}[/cyan]")

        # --- COMMIT FREQUENCY CHART ---
        plt.figure(figsize=(10, 4))
        plt.plot(sorted_months, counts, marker="o")
        plt.title("Commit Frequency Over Time")
        plt.xlabel("Month")
        plt.ylabel("Commits")
        plt.xticks(rotation=45)
        plt.tight_layout()
        chart_path = os.path.join("reports", "commit_frequency.png")
        plt.savefig(chart_path)
        plt.close()
        console.print(f"\n🖼️ Commit frequency chart saved to: [cyan]{chart_path}[/cyan]")

        # --- GENERATE MARKDOWN REPORT ---
        from git_repo_analyzer.report import generate_markdown_report
        report_path = generate_markdown_report(
            repo_path=repo_path,
            total_commits=len(commits),
            author_counts=dict(author_counts),
            chart_path=chart_path,
            language_chart_path=language_chart_path
        )
        console.print(f"📝 Markdown report saved to: [cyan]{report_path}[/cyan]")
        console.print("\n✅ [bold green]Analysis complete![/bold green]\n")

    finally:
        # If you want to automatically remove clones created for an analysis,
        # implement cleanup here. Currently we keep clones under ./cloned_repos/.
        pass
