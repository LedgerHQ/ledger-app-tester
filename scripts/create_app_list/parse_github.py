import requests
from dataclasses import dataclass, asdict
from typing import Dict, List

base_url = "https://api.github.com"
org_name = "LedgerHQ"

repos_endpoint = f"{base_url}/orgs/{org_name}/repos"


@dataclass
class Params:
    type: str
    archived: str
    sort: str
    page: int
    per_page: int


params = Params("public", "false", "full_name", 1, 100)


def parse_github(access_token: str = "") -> List[Dict[str, str]]:
    repos = []
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    while True:
        response = requests.get(repos_endpoint, params=asdict(params), headers=headers)
        repos_data = response.json()
        if not repos_data:  # No more repositories to fetch
            break
        for repo in repos_data:
            print(repo)
            if repo["archived"]:
                continue

            if repo["name"].lower().startswith("app-"):
                repo_name = repo["name"]
                owner_name = repo["owner"]["login"]
                repo_url = repo["html_url"]
                ref = repo["default_branch"]
                if repo["fork"]:
                    parent_response = requests.get(repo["url"],
                                                   headers=headers)
                    parent_data = parent_response.json()
                    if "parent" in parent_data:
                        owner_name = parent_data["parent"]["owner"]["login"]
                repos.append({"name": repo_name, "owner": owner_name, "ref": ref, "url": repo_url})

        params.page += 1

    return repos
