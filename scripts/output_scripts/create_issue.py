import requests
import json
from argparse import Namespace


def create_issue(github_access_token: str, pr_list: list):
    body = ""

    headers = {
        "Authorization": f"Bearer {github_access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    issue_endpoint = "https://api.github.com/repos/LedgerHQ/ledger-app-tester/issues"

    for pr in pr_list:
        body += f"- [ ] [{pr}]({pr}) \n"

    params = {
        "title": "[auto] Opened PRs",
        "body": body,
        "labels": ["auto"],
    }

    response = requests.post(issue_endpoint, headers=headers, json=params)
    print(response.json())
    if response.status_code == 201:
        print("Issue opened successfully")
    else:
        print(f"Failed opening issue {response.status_code}")


def main(args: Namespace) -> None:
    with open(args.input_file) as json_file:
        json_data = json.load(json_file)

    screenshot_pr_links = []

    for entry in json_data:
        if 'test' in entry and 'screenshot_pr_link' in entry['test']:
            screenshot_pr_links.append(entry['test']['screenshot_pr_link'])

    create_issue(args.access_token, screenshot_pr_links)
