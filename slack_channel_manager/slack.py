import functools
import re
import time
from urllib.parse import urlparse

import requests
from selenium import webdriver


################################################################################
# Helpers
################################################################################
@functools.lru_cache()
def get_slack_token(subdomain: str, d_cookie: str):
    """
    Get a session token based on the d cookie.
    https://papermtn.co.uk/retrieving-and-using-slack-cookies-for-authentication
    """
    response = requests.get(
        f"https://{subdomain}.slack.com",
        cookies={"d": d_cookie},
    )
    response.raise_for_status()

    match = re.search(r'"api_token":"([^"]+)"', response.text)
    if not match:
        raise ValueError("No api_token found in response")

    api_token = match.group(1)

    return api_token


def fetch_d_cookie(subdomain: str) -> str:
    driver = webdriver.Chrome()
    driver.get(f"https://{subdomain}.slack.com")

    while urlparse(driver.current_url).netloc != "app.slack.com":
        time.sleep(0.1)

    cookies = driver.get_cookies()
    d_cookie = next(
        cookie["value"]
        for cookie in cookies
        if cookie["domain"] == ".slack.com" and cookie["name"] == "d"
    )
    driver.quit()

    return d_cookie


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
