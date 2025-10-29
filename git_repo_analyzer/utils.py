EXCLUDE_DIRS = {".git", "venv", "__pycache__", "cloned_repos", ".idea", ".vscode"}
import os

def repo_files(root):
    for current, dirs, files in os.walk(root):
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            yield os.path.join(current, f)
