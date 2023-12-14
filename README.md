# slack-channel-manager

```sh
# First, clone the repo. Then...

# Setup your environment
brew install chromedriver --cask
poetry install

# Configure the tool
poetry run manager configure # follow the prompts
poetry run manager hey # should greet you by name

# Sort!
poetry run manager sort
```

This tool relies on several Slack APIs which do not appear in the slack API
documentation. It may break at any time.

No guarantee of CLI-command level stability is offered between various commits
to this tool.

## ⚠️ avoid Slack account takeovers

When you configure this tool, it fetches a potentially long-lived slack session
cookie and stores it in a file in this directory called `secret_config.json`.
Anyone with access to that cookie may interact with Slack on your behalf.

If you lose control of the file containing that cookie, or if someone else gains
access to is, [sign out of all Slack sessions](https://slack.com/help/articles/214613347-Sign-out-of-Slack)
immediately.
