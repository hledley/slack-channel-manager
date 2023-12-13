#!/usr/bin python

import functools
import json
import re
import time
from os import getenv

import click
from dotenv import load_dotenv

from slack_channel_manager.slack import (
    get_slack_client,
    get_slack_d_cookie,
    get_slack_token,
)


################################################################################
# Environment Access
################################################################################
@functools.lru_cache()
def _get_section_emoji() -> str:
    if emoji := getenv("SECTION_EMOJI"):
        return emoji

    raise ValueError("No emoji found. Please set SECTION_EMOJI env variable")


@functools.lru_cache()
def _get_section_name() -> str:
    if name := getenv("SECTION_NAME"):
        return name

    raise ValueError("No name found. Please set SECTION_NAME env variable")


@functools.lru_cache()
def _get_inc_regex() -> str:
    if regex := getenv("INCIDENT_REGEX"):
        return regex

    raise ValueError("No regex found. Please set INCIDENT_REGEX env variable")


################################################################################
# CLI
################################################################################
@click.group()
def cli():
    load_dotenv()


@cli.command()
def parse_d_cookie():
    click.echo(f"cookie: {get_slack_d_cookie()}")
    click.echo(f"token: {get_slack_token()}")


@cli.command()
def hey():
    profile = get_slack_client().get("/api/users.profile.get")
    click.echo(
        f"Hello {profile['profile']['display_name_normalized']} ({profile['profile']['email']})"
    )


@cli.command()
def incident_section():
    client = get_slack_client()

    # Ensure the section exists (and get its ID)
    # This API is undocumented. It appears to be paginated, but the mechanics
    # are unclear, and most users will have only one page of sections anyway.
    sections = client.get("/api/users.channelSections.list")["channel_sections"]
    channel_id_to_section_id: dict[str, str] = {}
    channel_section_id: str | None = None
    for section in sections:
        if section["name"] == _get_section_name():
            channel_section_id = section["channel_section_id"]
            click.echo(f"Found '{_get_section_name()}' section: {channel_section_id}")

            for channel_id in section["channel_ids_page"].get("channel_ids", []):
                # It is unclear how to fetch _additional_ pages of channel_ids,
                # but the first page should be sufficient for most users.
                channel_id_to_section_id[channel_id] = channel_section_id

    if not channel_section_id:
        # Create the section
        # This API is undocumented.
        channel_section_id = client.post(
            "/api/users.channelSections.create",
            data=[("name", _get_section_name()), ("emoji", _get_section_emoji())],
        )["channel_section_id"]
        click.echo(f"Created '{_get_section_name()}' section: {channel_section_id}")

    inc_regex = re.compile(_get_inc_regex())

    # Page through all available channels, adding any which are incidents _and_
    # you're in them to the incident section
    for page in client.paginated_get(
        "/api/conversations.list?exclude_archived=true&types=public_channel&limit=1000"
    ):
        page_inc_channels = [
            channel
            for channel in page["channels"]
            if channel["is_member"]
            and not channel_id_to_section_id.get(channel["id"])
            and inc_regex.match(channel["name"])
        ]

        if not page_inc_channels:
            time.sleep(0.25)  # slack has rate limits, let's naively wait a bit
            continue

        # Add the channels to the section
        # This API is undocumented.
        click.echo(
            f"Moving channels to incident section: {[channel['name'] for channel in page_inc_channels]}"
        )
        client.post(
            "/api/users.channelSections.channels.bulkUpdate",
            data=[
                (
                    "insert",
                    json.dumps(
                        [
                            {
                                "channel_section_id": channel_section_id,
                                "channel_ids": [
                                    channel["id"] for channel in page_inc_channels
                                ],
                            }
                        ]
                    ),
                )
            ],
        )

        time.sleep(0.25)  # slack has rate limits, let's naively wait a bit


if __name__ == "__main__":
    cli()
