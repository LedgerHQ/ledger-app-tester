from pathlib import Path
import requests
from utils import run_cmd


def create_branch(github_username: str, github_access_token: str, app_name: str, app_test_path: Path) -> bool:

    snapshot_path = Path(app_test_path) / "snapshots"

    if not snapshot_path.exists():
        return False

    error, output = run_cmd("git status --porcelain .", snapshot_path, no_throw=True)

    if output:
        run_cmd("git config user.name 'Ledger App Tester Bot'", cwd=snapshot_path)
        run_cmd("git config user.email 'noreply.github.com'", cwd=snapshot_path)
        run_cmd("git checkout auto-update-screenshots 2>/dev/null || git checkout -b auto-update-screenshots",
                cwd=snapshot_path)
        run_cmd("git add .", cwd=snapshot_path)
        run_cmd("git -c commit.gpgsign=false commit -m '[auto] Update screenshot'",
                cwd=snapshot_path)
        run_cmd(f"git push --set-upstream \
                https://{github_username}:{github_access_token}@github.com/LedgerHQ/{app_name} \
                auto-update-screenshots --force", cwd=snapshot_path)
        return True

    return False


def create_pr(github_access_token: str, app_name: str) -> str:
    headers = {
        "Authorization": f"Bearer {github_access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "title": "[auto] Update Screenshots",
        "body": "Please review changes !",
        "head": "auto-update-screenshots",
        "base": "develop",
        "labels": ["auto"],
    }
    pr_endpoint = f"https://api.github.com/repos/LedgerHQ/{app_name}/pulls"

    response = requests.post(pr_endpoint, headers=headers, json=params)
    if response.status_code == 201:
        print(f"PR for {app_name} opened successfully")
        repos_data = response.json()
        return repos_data['html_url']

    if response.status_code == 422:
        print(f"PR for {app_name} exists")
    else:
        print(f"Creating PR for {app_name} failed {response.status_code}")
    return ""


def create_prs(github_username: str, github_access_token: str, app_json: dict, workdir: Path) -> str:
    output = ""
    repo_name = app_json["name"]
    app_test_path = workdir / Path(repo_name + "/" + app_json.get("test_dir", "."))

    branch_created = create_branch(github_username, github_access_token, repo_name, app_test_path)

    if branch_created:
        output = create_pr(github_access_token, repo_name)

    return output
