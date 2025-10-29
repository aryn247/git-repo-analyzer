# git_repo_analyzer/analyzer.py

import os
import json
from collections import Counter
from datetime import datetime
from typing import Tuple, Dict, Optional, Union

from rich.console import Console
from git import Repo, GitCommandError, InvalidGitRepositoryError

console = Console()

# Optional imports (fallback if modules missing)
try:
    from git_repo_analyzer.file_scanner import analyze_files
except ImportError:
    analyze_files = None

try:
    from git_repo_analyzer.report_builder import generate_html_report
except ImportError:
    generate_html_report = None

try:
    from git_repo_analyzer.repo_scanner import scan_repo
except ImportError:
    scan_repo = None

try:
    from git_repo_analyzer.report import generate_markdown_report as md_report
except ImportError:
    md_report = None


def is_git_url(s: str) -> bool:
    return bool(s and (s.startswith("http://") or s.startswith("https://") or s.endswith(".git")))


def clone_repo_from_url(url: str) -> str:
    base_dir = os.path.abspath("cloned_repos")
    os.makedirs(base_dir, exist_ok=True)

    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = os.path.join(base_dir, f"{repo_name}_{timestamp}")

    console.print(f"[yellow]Cloning {url} → {dest}[/yellow]")
    Repo.clone_from(url, dest)

    return dest


def get_language_usage(repo_path: str) -> Dict[str, int]:
    from pygments.lexers import guess_lexer_for_filename
    from pygments.util import ClassNotFound

    language_sizes = {}
    for root, dirs, files in os.walk(repo_path):
        if ".git" in dirs:
            dirs.remove(".git")

        for f in files:
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf8", errors="ignore") as fh:
                    content = fh.read(8192)
                lexer = guess_lexer_for_filename(f, content)
                language = lexer.name
                size = os.path.getsize(path)
                language_sizes[language] = language_sizes.get(language, 0) + size
            except (OSError, UnicodeDecodeError, ClassNotFound):
                pass

    return language_sizes


def write_json_report(report_obj: dict, out_path: str):
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report_obj, fh, indent=2, default=str)


def reports_dir_for_repo(repo_path: str) -> str:
    d = os.path.join(repo_path, ".analysis_reports")
    os.makedirs(d, exist_ok=True)
    return d


def analyze_repository(
    repo_source: Union[str, Tuple[str, str]],
    report: Optional[str] = None,
    show_branches: bool = False,
    complexity: bool = False,
):
    """Main repository analysis entry point"""

    # Determine local path or URL
    if isinstance(repo_source, tuple):
        mode, value = repo_source
    else:
        mode = "url" if is_git_url(repo_source) else "local"
        value = repo_source

    repo_path = None

    try:
        # Clone if URL
        if mode == "url":
            repo_path = clone_repo_from_url(value)
        else:
            repo_path = os.path.abspath(value)

        try:
            repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            console.print(f"[red]Not a valid git repo: {repo_path}[/red]")
            return None

        # Collect commit + author info
        commits = list(repo.iter_commits())
        authors = [c.author.name if c.author else "Unknown" for c in commits]
        author_counts = dict(Counter(authors))

        commit_dates = [datetime.fromtimestamp(c.committed_date) for c in commits]

        repo_results = {
            "path": repo_path,
            "total_commits": len(commits),
            "authors": author_counts,
            "commit_dates": commit_dates,
        }

        if show_branches:
            repo_results["branches"] = [b.name for b in repo.branches]

        console.print(f"\n📊 [bold blue]Repo Analysis[/bold blue]")
        console.print(f"[green]Path:[/green] {repo_path}")
        console.print(f"[green]Total commits:[/green] {repo_results['total_commits']}")
        console.print(f"[green]Unique authors:[/green] {len(author_counts)}")

        # Optional complexity scan
        file_complexity = analyze_files(repo_path) if complexity and analyze_files else None
        if complexity:
            console.print(f"[cyan]Complexity scan completed[/cyan]")

        language_sizes = get_language_usage(repo_path)
        console.print(f"[green]Detected languages:[/green] {', '.join(language_sizes.keys())}")

        # ==============================
        # REPORT GENERATION
        # ==============================
        if report:
            reports_dir = reports_dir_for_repo(repo_path)
            repo_name = os.path.basename(repo_path)

            report_data = {
                "repo": repo_results,
                "complexity": file_complexity,
                "languages": language_sizes,
                "generated_at": datetime.utcnow().isoformat(),
            }

            ext = report.lower()

            # JSON report
            if ext == "json":
                out = os.path.join(reports_dir, f"{repo_name}_report.json")
                write_json_report(report_data, out)
                console.print(f"✅ JSON saved → {out}")

            # Markdown report
            if ext in ("md", "markdown"):
                if md_report:
                    out = md_report(repo_path,
                                    repo_results["total_commits"],
                                    author_counts,
                                    commit_dates,
                                    None)
                else:
                    out = os.path.join(reports_dir, f"{repo_name}_report.md")
                    with open(out, "w", encoding="utf-8") as fh:
                        fh.write(f"# Repo Analysis: {repo_name}\n")
                        fh.write(f"- Total commits: {repo_results['total_commits']}\n")
                console.print(f"✅ Markdown saved → {out}")

            # HTML report
            if ext == "html":
                if generate_html_report:
                    out = os.path.join(reports_dir, f"{repo_name}_report.html")
                    generate_html_report(
    repo_name,
    repo_results["total_commits"],
    author_counts,
    output_file=out,
    commit_dates=commit_dates,
    language_sizes=language_sizes,
    file_complexity=file_complexity,
    branches=repo_results.get("branches"),
)

                    console.print(f"✅ HTML saved → {out}")
                else:
                    console.print("[yellow]HTML reporting not available — missing report_builder[/yellow]")

        console.print("\n✅ [bold green]Analysis complete![/bold green]")
        return {"repo": repo_results, "languages": language_sizes, "complexity": file_complexity}

    except GitCommandError as e:
        console.print(f"[red]Git Error: {e}[/red]")
        return None
