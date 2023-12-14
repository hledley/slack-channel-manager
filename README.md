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
