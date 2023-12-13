# slack-channel-manager

```
poetry install
poetry run manager --help
```

## Usage

- clone repo
- `poetry install`
- create a `.env` file in the base of the repo
  ```
  SLACK_SUBDOMAIN=<subdomain>
  SECTION_NAME=<name>
  SECTION_EMOJI=<emoji>
  INCIDENT_REGEX=<regex>
  SLACK_D_COOKIE=<token>
  ```
  - set `SLACK_SUBDOMAIN` to your slack subdomain: `foo` for `foo.slack.com`
  - set `SECTION_NAME` to the name of the section to look for or create (like `incidents`)
  - set `SECTION_EMOJI` to the name of the emoji to use for the section icon if it is created (like `plus`, not `:plus:`)
  - set `INCIDENT_REGEX` to a regex for channels you want to sort (e.g., `(inc-)|(incident-)`)
  - set `SLACK_D_COOKIE` to the value of the `d` cookie pulled from your browser cookiejar on `<subdomain>.slack.com`
- `poetry run manager hey` - should greet you by name
- `poetry run manager incident-section`
