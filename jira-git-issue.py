#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import re
import sys
import json
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
import argparse

SECRETS_PATH = Path.home() / ".jira_secrets.json"
JIRA_ISSUES_FILE = ".jira-issues.json"


def get_issue_data(*, issue_key):
    """Fetch issue data from Jira or cache, if cached."""

    top_level = get_git_repo_path()
    issue_file_path = f"{top_level}/{JIRA_ISSUES_FILE}"
    issue_path = Path(issue_file_path)

    if not issue_path.exists():
        print(
            f"No Jira issues file found at {issue_file_path}. Please register your Jira domain and secrets first.",
            file=sys.stderr,
        )
        sys.exit(7)
    with issue_path.open("r") as f:
        data = json.load(f)
    if not "issues" in data:
        data["issues"] = {}

    if issue_key in data["issues"]:
        if "summary" in data["issues"][issue_key]:
            return data["issues"][issue_key]["summary"]

    secrets = get_project_secrets()
    jira_data = get_issue_data_from_jira(
        cloud_id=secrets["cloud_id"],
        issue_key=issue_key,
        api_token=secrets["api_key"],
        email=secrets["email"],
    )
    summary = jira_data["fields"]["summary"]
    if not issue_key in data["issues"]:
        data["issues"][issue_key] = {}

    data["issues"][issue_key]["summary"] = summary
    with issue_path.open("w") as f:
        issue_path.write_text(json.dumps(data, indent=4))
    return summary


def get_issue_data_from_jira(*, cloud_id, issue_key, api_token, email):
    """Fetch issue data from Jira."""
    # Won't allow me to limit by ?fields= gives 401 scope does not match
    JIRA_URL = f"https://api.atlassian.com/ex/jira/{cloud_id}"
    ISSUE_KEY = issue_key
    API_TOKEN = api_token
    EMAIL = email

    url = f"{JIRA_URL}/rest/api/3/issue/{ISSUE_KEY}"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(EMAIL, API_TOKEN),
        headers={"Accept": "application/json"},
    )

    if response.status_code == 200:
        issue = response.json()
        return issue
    else:
        print(
            f"Failed to fetch issue: {response.status_code} - {response.text}",
            file=sys.stderr,
        )


def get_git_repo_path():
    """Get the top-level directory of the git repository."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        return None


def get_current_issue():
    """Get the current git branch name."""

    # Get the current branch name
    try:
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        sys.exit(10)

    # Match the branch name to the pattern 'issue/<alphanumeric>'
    match = re.match(r"^issue/jira/([a-zA-Z0-9]+-\d+)$", branch)
    if match:
        issue_key = match.group(1)
    else:
        sys.exit(11)

    return issue_key


def get_secrets(domain):
    """Retrieve the cloudId, email and API key for the given Jira domain."""

    if not SECRETS_PATH.exists():
        print(
            f"No secrets file found at {SECRETS_PATH}. Please register your Jira domain and API key.",
            file=sys.stderr,
        )
        sys.exit(2)

    with open(SECRETS_PATH, "r") as f:
        secrets = json.load(f)

    if domain not in secrets:
        print(
            f"No API key found for domain {domain}. Please register it first.",
            file=sys.stderr,
        )
        sys.exit(3)

    return secrets[domain]


def register_secret(domain, email, api_key):
    """Register the Jira domain, email and API key."""

    url = f"https://{domain}.atlassian.net/_edge/tenant_info"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(email, api_key),
        headers={"Accept": "application/json"},
    )

    cloud_id = None
    if response.status_code == 200:
        data = response.json()
        cloud_id = data.get("cloudId")
    else:
        print(
            "Failed to fetch tenant info:",
            response.status_code,
            response.text,
            file=sys.stderr,
        )
        sys.exit(4)

    if not SECRETS_PATH.exists():
        SECRETS_PATH.write_text(json.dumps({}))

    with open(SECRETS_PATH, "r") as f:
        secrets = json.load(f)

    secrets[domain] = {
        "email": email,
        "api_key": api_key,
        "cloud_id": cloud_id,
    }

    with open(SECRETS_PATH, "w") as f:
        json.dump(secrets, f, indent=4)

    print(f"Registered {domain} with provided email and API key.")


def register_project(domain):
    """Register the Jira project domain."""

    top_level = get_git_repo_path()
    if not top_level:
        print("Not in a git repository.", file=sys.stderr)
        sys.exit(10)

    issue_file = f"{top_level}/{JIRA_ISSUES_FILE}"

    issue_path = Path(issue_file)

    if not issue_path.exists():
        issue_path.write_text(json.dumps({}))

    secrets = get_secrets(domain)
    if not secrets:
        print(
            f"No API key found for domain {domain}. Please register it first.",
            file=sys.stderr,
        )
        sys.exit(20)

    with issue_path.open("r") as f:
        data = json.load(f)

    if domain in data:
        print(
            f"{domain} is already registered. Will replace the existing entry.",
            file=sys.stderr,
        )

    data["domain"] = domain

    with issue_path.open("w") as f:
        issue_path.write_text(json.dumps(data, indent=4))

    print(f"Registered {domain} (found API key).")


def get_project_secrets():
    """Get the secrets for the current git project."""
    top_level = get_git_repo_path()
    if not top_level:
        print("Not in a git repository.", file=sys.stderr)
        sys.exit(10)

    issue_file = f"{top_level}/{JIRA_ISSUES_FILE}"
    issue_path = Path(issue_file)

    if not issue_path.exists():
        print(
            f"No Jira issues file found at {issue_file}. Please register your Jira domain first.",
            file=sys.stderr,
        )
        sys.exit(5)

    with issue_path.open("r") as f:
        data = json.load(f)

    if "domain" not in data:
        print(
            "No Jira domain registered for this project. Please register it first.",
            file=sys.stderr,
        )
        sys.exit(6)

    return get_secrets(data["domain"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Jira issue viewing utility with git branches"
    )
    parser.add_argument(
        "--register-secrets",
        nargs=3,
        metavar=("domain", "email", "api_key"),
        help="Register Jira domain, email, and API key",
    )
    parser.add_argument(
        "--register-project",
        nargs=1,
        metavar=("domain"),
        help="Register Jira domain for the current git project",
    )
    parser.add_argument(
        "--view-git-issue",
        action="store_true",
        help="View the current Jira issue based on the current git branch name",
    )
    args = parser.parse_args()

    if args.register_secrets:
        domain, email, api_key = args.register_secrets
        register_secret(domain, email, api_key)
    elif args.register_project:
        domain = args.register_project[0]
        register_project(domain)
    elif args.view_git_issue:
        print(get_issue_data(issue_key=get_current_issue()))
    else:
        parser.print_help()
        sys.exit(1)
