# git_repo_analyzer/report_builder.py
import os
from datetime import datetime
from typing import Dict, Optional, Any, List

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator

# Ensure non-interactive backend (safe for CLI environments)
plt.switch_backend("Agg")


def _ensure_dirs(reports_dir: str):
    charts_dir = os.path.join(reports_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    return charts_dir


def _safe_basename(path: str) -> str:
    return os.path.basename(path).replace(" ", "_")


def build_commit_frequency_chart(commit_dates: List[str], out_path: str):
    """
    commit_dates: list of ISO-format date strings (YYYY-MM-DD...).
    Produces a monthly commits line chart (PNG).
    """
    if not commit_dates:
        return None

    # Convert ISO-ish strings to datetime.date where possible
    parsed = []
    for s in commit_dates:
        try:
            # Accept full ISO datetimes or YYYY-MM
            parsed.append(datetime.fromisoformat(s))
        except Exception:
            try:
                parsed.append(datetime.strptime(s, "%Y-%m"))
            except Exception:
                continue

    if not parsed:
        return None

    # Aggregate by month (YYYY-MM)
    monthly = {}
    for d in parsed:
        key = d.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + 1

    keys = sorted(monthly.keys())
    values = [monthly[k] for k in keys]

    # Plot
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(keys, values, marker="o", linewidth=2)
    ax.set_title("Commits per Month")
    ax.set_xlabel("")
    ax.set_ylabel("Commits")
    ax.grid(alpha=0.12)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8))
    fig.autofmt_xdate(rotation=30)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def build_language_pie(language_sizes: Dict[str, int], out_path: str):
    """
    language_sizes: mapping language -> bytes
    Produces a pie chart.
    """
    if not language_sizes:
        return None

    # Keep top 8 languages; aggregate rest into "Other"
    items = sorted(language_sizes.items(), key=lambda t: t[1], reverse=True)
    top = items[:8]
    other = items[8:]
    labels = [t[0] for t in top]
    sizes = [t[1] for t in top]
    if other:
        labels.append("Other")
        sizes.append(sum(v for _, v in other))

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=140)
    ax.set_title("Language Usage (by bytes)")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def build_complexity_table_html(file_complexity: Dict[str, Any], max_rows: int = 20) -> str:
    """
    file_complexity: mapping file -> complexity info (lines, funcs, or radon metrics)
    Returns an HTML table (string) with top N by complexity heuristic.
    """
    if not file_complexity:
        return "<p>No complexity data available.</p>"

    # Normalize items to have a score: prefer radon 'complexity' or use funcs*lines heuristic
    rows = []
    for f, meta in file_complexity.items():
        score = None
        lines = meta.get("lines") if isinstance(meta, dict) else None
        funcs = meta.get("functions") or meta.get("funcs") or meta.get("func_count") or 0
        if isinstance(meta, dict) and "complexity" in meta:
            try:
                score = float(meta["complexity"])
            except Exception:
                score = None
        if score is None:
            try:
                score = funcs * (lines / 100 if lines else 1)
            except Exception:
                score = 0
        rows.append((f, score, lines or "-", funcs or 0))

    rows.sort(key=lambda r: r[1], reverse=True)
    display = rows[:max_rows]

    table = "<table class='table'><thead><tr><th>File</th><th>Score</th><th>Lines</th><th>Funcs</th></tr></thead><tbody>"
    for f, score, lines, funcs in display:
        table += f"<tr><td class='mono'>{f}</td><td>{float(score):.1f}</td><td>{lines}</td><td>{funcs}</td></tr>"
    table += "</tbody></table>"
    return table


def build_branches_html(branches: Optional[Dict[str, Any]]) -> str:
    if not branches:
        return "<p>No branch information available.</p>"
    # branches may be list or dict
    if isinstance(branches, list):
        # just names
        lis = "".join(f"<li>{b}</li>" for b in branches)
        return f"<ul class='branch-list'>{lis}</ul>"
    elif isinstance(branches, dict):
        lis = ""
        for name, info in branches.items():
            commit_count = info.get("commit_count", "N/A")
            latest = info.get("latest", "N/A")
            lis += f"<li><strong>{name}</strong> — {commit_count} commits — latest: {latest}</li>"
        return f"<ul class='branch-list'>{lis}</ul>"
    else:
        return "<p>Branches: unknown format</p>"


def generate_html_report(
    repo_name: str,
    commit_count: int,
    authors: Dict[str, int],
    output_file: str,
    commit_dates: Optional[List[datetime]] = None,
    language_sizes: Optional[Dict[str, int]] = None,
    file_complexity: Optional[Dict[str, Any]] = None,
    branches: Optional[List[str]] = None,
) -> str:
    """Generate a complete HTML report including charts."""

    reports_dir = os.path.dirname(output_file)
    charts_dir = _ensure_dirs(reports_dir)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    commit_img = None
    if commit_dates:
        commit_img = os.path.join(charts_dir, f"{repo_name}_commits_{timestamp}.png")
        iso_dates = [d.isoformat() if isinstance(d, datetime) else str(d) for d in commit_dates]
        build_commit_frequency_chart(iso_dates, commit_img)

    language_img = None
    if language_sizes:
        language_img = os.path.join(charts_dir, f"{repo_name}_languages_{timestamp}.png")
        build_language_pie(language_sizes, language_img)

    complexity_table = build_complexity_table_html(file_complexity or {}, max_rows=25)
    branches_html = build_branches_html(branches)

    author_items = "".join(f"<li>{name}: {count}</li>" for name, count in authors.items())

    html_content = f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Repo Analysis - {repo_name}</title>
<style>
 body {{
   background: #111;
   color: #e0e0e0;
   font-family: Arial, sans-serif;
   padding: 20px;
 }}
 h1, h2 {{
   color: #4aa3ff;
 }}
 .card {{
   background: #1a1a1a;
   border-radius: 10px;
   padding: 15px;
   margin: 15px 0;
   border: 1px solid #333;
 }}
 img {{
   max-width: 700px;
   border: 1px solid #333;
   border-radius: 6px;
 }}
 footer {{
   margin-top: 30px;
   opacity: .6;
   font-size: 12px;
 }}
 table {{
   color: #fff;
   width: 100%;
   border-collapse: collapse;
 }}
 th, td {{
   border: 1px solid #333;
   padding: 6px;
 }}
</style>
</head>
<body>

<h1>📊 Repository Report — {repo_name}</h1>
<p><strong>Total Commits:</strong> {commit_count}</p>

<div class="card">
<h2>👤 Authors</h2>
<ul>{author_items}</ul>
</div>

<div class="card">
<h2>🧭 Branches</h2>
{branches_html}
</div>

<div class="card">
<h2>📈 Commit Activity</h2>
{"<img src='" + os.path.relpath(commit_img, reports_dir) + "'>" if commit_img else "<p>No commit timeline available.</p>"}
</div>

<div class="card">
<h2>🗂 Language Breakdown</h2>
{"<img src='" + os.path.relpath(language_img, reports_dir) + "'>" if language_img else "<p>No language stats available.</p>"}
</div>

<div class="card">
<h2>🧠 Complexity Overview</h2>
{complexity_table}
</div>

<footer>Generated by git-repo-analyzer — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</footer>

</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(html_content)

    return output_file
