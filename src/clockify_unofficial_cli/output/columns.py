from typing import Final

from clockify_unofficial_cli.output.renderer import Column

AUTH_STATUS: Final = (
    Column("profile", "Profile"),
    Column("name", "User"),
    Column("email", "Email"),
    Column("workspaceId", "Workspace"),
    Column("region", "Region"),
    Column("source", "Credential source"),
    Column("apiKey", "API key"),
)

PROFILES: Final = (
    Column("name", "Profile"),
    Column("default", "Default"),
    Column("region", "Region"),
    Column("workspaceId", "Workspace"),
    Column("email", "Email"),
)

WORKSPACES: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
)

USERS: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("email", "Email"),
    Column("status", "Status"),
)

CLIENTS: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("email", "Email"),
    Column("archived", "Archived"),
)

PROJECTS_LIST: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("clientId", "Client"),
    Column("public", "Public"),
    Column("billable", "Billable"),
    Column("archived", "Archived"),
)

TAGS: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("archived", "Archived"),
)

TASKS: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("status", "Status"),
    Column("assigneeIds", "Assignees"),
    Column("estimate", "Estimate"),
)

CUSTOM_FIELDS: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("type", "Type"),
    Column("entityType", "Entity"),
    Column("status", "Status"),
)

GROUPS: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("userIds", "Members"),
)

TIME_ENTRIES: Final = (
    Column("id", "ID"),
    Column("description", "Description"),
    Column("projectId", "Project"),
    Column("taskId", "Task"),
    Column("timeInterval.start", "Start"),
    Column("timeInterval.end", "End"),
    Column("timeInterval.duration", "Duration"),
    Column("billable", "Billable"),
)

WEBHOOKS: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("url", "URL"),
    Column("webhookEvent", "Event"),
    Column("triggerSourceType", "Source type"),
    Column("enabled", "Enabled"),
)

WEBHOOKS_WITH_TOKEN: Final = (*WEBHOOKS, Column("authToken", "Signing token"))

WEBHOOK_LOGS: Final = (
    Column("id", "ID"),
    Column("statusCode", "Status"),
    Column("respondedAt", "Responded at"),
    Column("webhookEventStatusId", "Event status"),
)

WEBHOOK_STATUSES: Final = (
    Column("id", "ID"),
    Column("status", "Status"),
    Column("statusCode", "HTTP"),
    Column("retryCount", "Retries"),
    Column("respondedAt", "Responded at"),
)

REPORT_GROUPS: Final = (
    Column("level", "Level"),
    Column("id", "ID"),
    Column("name", "Name"),
    Column("duration", "Seconds"),
)

REPORT_ENTRIES: Final = (
    Column("_id", "ID"),
    Column("description", "Description"),
    Column("userName", "User"),
    Column("projectName", "Project"),
    Column("timeInterval.start", "Start"),
    Column("timeInterval.end", "End"),
    Column("timeInterval.duration", "Seconds"),
    Column("billable", "Billable"),
)
