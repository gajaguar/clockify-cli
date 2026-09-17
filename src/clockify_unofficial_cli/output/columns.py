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
