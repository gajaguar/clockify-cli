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
