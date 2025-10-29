from .utils import repo_files

def scan_complexity(file_path: str) -> dict:
    """
    Very simple fallback complexity scan if radon isn't installed.
    Counts number of lines and function declarations.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lines = content.count("\n") + 1
        funcs = (
            content.count("def ") +
            content.count("function ") +
            content.count("func ")
        )
        return {"lines": lines, "functions": funcs}
    except:
        return {}

def analyze_files(repo_path):
    results = {}

    for file_path in repo_files(repo_path):
        results[file_path] = scan_complexity(file_path)

    return results
