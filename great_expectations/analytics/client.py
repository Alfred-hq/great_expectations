from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import posthog

from great_expectations.analytics.config import ENV_CONFIG, Config, update_config

if TYPE_CHECKING:
    from great_expectations.analytics.base_event import Event


def submit(event: Event) -> None:
    """Sends the analytics event to our analytics platform.

    Args:
        event: An object containing the details of the event to be submitted.
    """

    try:
        groups = {
            "data_context": event.data_context_id,
        }
        if event.organization_id:
            groups.update({"organization": event.organization_id})

        posthog.capture(
            str(event.distinct_id),
            str(event.action),
            event.properties(),
            groups=groups,
        )
    except Exception as _:
        # failure to send an analytics event should not be propagated to user
        # TODO: figure out what to do about undeliverable events
        pass


def init(  # noqa: PLR0913
    enable: bool,
    user_id: Optional[UUID] = None,
    data_context_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    oss_id: Optional[UUID] = None,
    cloud_mode: bool = False,
):
    """Initializes the analytics platform client."""
    conf = {}
    if user_id:
        conf["user_id"] = user_id
    if data_context_id:
        conf["data_context_id"] = data_context_id
    if organization_id:
        conf["organization_id"] = organization_id
    if oss_id:
        conf["oss_id"] = oss_id
    update_config(config=Config(cloud_mode=cloud_mode, **conf))

    enable = enable and not _in_gx_ci()
    posthog.disabled = not enable
    if enable:
        posthog.debug = ENV_CONFIG.posthog_debug
        posthog.project_api_key = ENV_CONFIG.posthog_project_api_key
        posthog.host = ENV_CONFIG.posthog_host


def _in_gx_ci() -> bool:
    """
    To prevent polluting analytics data with CI runs, we disable analytics tracking when running in
    certain environments (GitHub Actions and Azure Pipelines).

    We also disable analytics tracking when running tests with Pytest to prevent issues during local
    development.
    """
    return (
        # GitHub Actions: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
        os.getenv("GITHUB_REPOSITORY") == "great-expectations/great_expectations"
        # Azure Pipelines: https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops&tabs=yaml#system-variables-devops-services
        or os.getenv("System.TeamProject") == "great_expectations"
        # Pytest: https://docs.pytest.org/en/7.1.x/example/simple.html#pytest-current-test-environment-variable
        or bool(os.getenv("PYTEST_CURRENT_TEST"))
    )
