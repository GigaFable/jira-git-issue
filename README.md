# jira-git-issue

A command-line utility to fetch and display the summary of the current Jira issue based on your git branch. Designed for use in your shell prompt (e.g., with Oh My Posh) to show the current issue summary as you work.

## Features

- Fetches the current Jira issue summary based on the git branch name (expects branch names like `issue/jira/PROJECT-123`)
- Caches issue summaries for faster repeated lookups
- Supports registering multiple Jira domains and API credentials
- Integrates easily with shell prompts for developer productivity

## Installation

1. Clone this repository or copy `jira-git-issue.py` to your project or somewhere in your `$PATH`.
2. Ensure you have Python 3 and `requests` installed:
   ```bash
   pip install requests # Or let the system package manager, i.e. apt install it
   ```

## Setup

1. Goto [this](https://id.atlassian.com/manage-profile/security/api-tokens) URL and create an API token with the scope `read:jira-work`.
2. Copy the API key. You need it for the next step
3. Register your Jira API credentials (domain, email, API key):

   Note: `domain` is just the part before .atlassian.net in the URL of your JIRA. So if your JIRA was at `https://monkeyland.atlassian.net/`, `domain` (when used below) is just `monkeyland`. Email is the email of the user you used to generate the API key as registered with JIRA.

   ```bash
   ./jira-git-issue.py --register-secrets <domain> <email> <api_key>
   ```

   Example:

   ```bash
   ./jira-git-issue.py --register-secrets monkeyland user@company.com my_api_token
   ```

4. Register your Jira domain for the current git project (must be done inside a git project directory or subdirectory):
   ```bash
   ./jira-git-issue.py --register-project <domain>
   ```

## Usage

- To fetch and print the summary of the current Jira issue (based on the current git branch):
  ```bash
  ./jira-git-issue.py --view-git-issue
  ```
- You can add this to your shell prompt (e.g., with Oh My Posh) to display the current issue summary automatically.

## Branch Naming Convention

- Branches should be named like `issue/jira/PROJECT-123` for the tool to extract the Jira issue key.

## Example Prompt Integration (Oh My Posh)

Add a custom segment to your Oh My Posh config that runs:

```bash
$(jira-git-issue.py --view-git-issue)
```

Here is an example of a block I added to the blocks section of my theme to put it on a new line below my main prompt line:

```json
    {
      "alignment": "left",
      "newline": true,
      "segments": [
        {
          "type": "command",
          "style": "diamond",
          "background": "#341948",
          "foreground": "#EFDCF9",
          "trailing_diamond": "\ue0b4",
          "properties": {
            "script": "~/bin/jira-git-issue.py --view-git-issue",
            "shell": "bash"
          },
          "template": " \uE0A0 {{ .Output }} \uE0A0"
        }
      ],
      "type": "prompt"
    },
```

## Troubleshooting

- Make sure your Jira API token has the correct permissions.
- Ensure your branch name matches the expected pattern.
- If you change projects, re-register the Jira domain for each git repo.

## License

MIT
