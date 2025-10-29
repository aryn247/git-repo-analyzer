# git_repo_analyzer/report.py
import os
from datetime import datetime
from typing import Dict, Optional

def generate_markdown_report(
    repo_path: str,
    total_commits: int,
    author_counts: Dict[str, int],
    chart_path: str,
    language_chart_path: Optional[str] = None
) -> str:
    """
    Generate a REPORT.md inside ./reports and return the path to the report file.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 🧠 Git Repository Analysis Report",
        "",
        f"**Repository Path:** `{repo_path}`  ",
        f"**Generated on:** {now}",
        "",
        "---",
        "## 📌 Summary",
        "",
        f"- **Total commits:** {total_commits}",
        f"- **Unique contributors:** {len(author_counts)}",
        "",
        "---",
        "## 👥 Contributors",
        "",
        "| Author | Commits |",
        "|--------|---------|",
    ]

    # Add each author’s data
    for author, count in sorted(author_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {author} | {count} |")

    lines += [
        "",
        "---",
        "## 🕒 Commit Frequency",
        "",
        f"![Commit Frequency Chart]({chart_path})",
    ]

    if language_chart_path:
        lines += [
            "",
            "---",
            "## 🖥️ Language Usage",
            "",
            f"![Language Usage Chart]({language_chart_path})",
        ]

    lines += [
        "",
        "---",
        "✅ *Generated automatically by Git Repository Analyzer*",
        "",
    ]

    os.makedirs("reports", exist_ok=True)
    report_path = os.path.join("reports", "REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_path
