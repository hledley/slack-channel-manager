import functools
import re
from os import getenv

import click
import requests


################################################################################
# Environment Access
################################################################################
@functools.lru_cache()
def _get_slack_subdomain():
    if domain := getenv("SLACK_SUBDOMAIN"):
        return domain

    raise ValueError("No domain found. Please set SLACK_SUBDOMAIN env variable")


@functools.lru_cache()
def get_slack_d_cookie():
    if cookie := getenv("SLACK_D_COOKIE"):
        return cookie

    raise ValueError("No cookie found. Please set SLACK_D_COOKIE env variable.")


################################################################################
# Helpers
################################################################################
@functools.lru_cache()
def get_slack_client() -> "SlackRequestClient":
    return SlackRequestClient(
        subdomain=_get_slack_subdomain(),
        token=get_slack_token(),
        cookie=get_slack_d_cookie(),
    )


@functools.lru_cache()
def get_slack_token():
    """
    Get a session token based on the d cookie.
    https://papermtn.co.uk/retrieving-and-using-slack-cookies-for-authentication
    """
    response = requests.get(
        f"https://{_get_slack_subdomain()}.slack.com",
        cookies={"d": get_slack_d_cookie()},
    )
    response.raise_for_status()

    match = re.search(r'"api_token":"([^"]+)"', response.text)
    if not match:
        click.echo("No api_token found in response")
        return 1

    api_token = match.group(1)

    return api_token


################################################################################
# Slack API Client
################################################################################
def _slack_raise_for_status(response: requests.Response):
    response.raise_for_status()
    if not response.json()["ok"]:
        print(response.request.body)
        print(response.text)

        raise Exception("non-OK slack response")


class SlackRequestClient:
    def __init__(self, subdomain: str, token: str, cookie: str):
        self.subdomain = subdomain

        self.session = requests.session()
        self.session.cookies["d"] = cookie
        self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, path: str, **kwargs) -> dict:
        assert path and path[0] == "/"

        response = self.session.get(
            f"https://{self.subdomain}.slack.com{path}", **kwargs
        )

        _slack_raise_for_status(response)
        return response.json()

    def paginated_get(self, path: str, **kwargs) -> dict:
        assert path and path[0] == "/" and "?" in path

        response = self.session.get(
            f"https://{self.subdomain}.slack.com{path}", **kwargs
        )
        _slack_raise_for_status(response)

        while cursor := response.json().get("response_metadata", {}).get("next_cursor"):
            yield response.json()

            response = self.session.get(
                f"https://{self.subdomain}.slack.com{path}&cursor={cursor}", **kwargs
            )
            _slack_raise_for_status(response)

        return response.json()

    def post(self, path: str, data: list[tuple], **kwargs) -> dict:
        assert path and path[0] == "/"

        response = self.session.post(
            f"https://{self.subdomain}.slack.com{path}",
            data,
            **kwargs,
        )
        _slack_raise_for_status(response)

        return response.json()
