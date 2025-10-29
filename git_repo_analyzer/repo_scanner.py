from git import Repo

def scan_repo(repo_path):
    repo = Repo(repo_path)

    commits = get_all_commits(repo)
    branches = branch_statistics(repo)

    return {
        "commit_count": len(commits),
        "branches": branches,
    }
