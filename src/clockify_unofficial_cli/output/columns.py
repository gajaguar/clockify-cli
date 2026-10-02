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

TIME_OFF_POLICIES: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("timeUnit", "Unit"),
    Column("archived", "Archived"),
    Column("allowHalfDay", "Half days"),
    Column("approve.requiresApproval", "Needs approval"),
)

TIME_OFF_REQUESTS: Final = (
    Column("id", "ID"),
    Column("userName", "User"),
    Column("policyName", "Policy"),
    Column("status.statusType", "Status"),
    Column("timeOffPeriod.period.start", "Start"),
    Column("timeOffPeriod.period.end", "End"),
    Column("balanceDiff", "Balance change"),
)

TIME_OFF_REQUEST_RESULT: Final = (
    Column("id", "ID"),
    Column("userId", "User"),
    Column("policyId", "Policy"),
    Column("status.statusType", "Status"),
    Column("timeOffPeriod.period.start", "Start"),
    Column("timeOffPeriod.period.end", "End"),
    Column("balanceDiff", "Balance change"),
)

TIME_OFF_BALANCES: Final = (
    Column("userName", "User"),
    Column("policyName", "Policy"),
    Column("balance", "Balance"),
    Column("used", "Used"),
    Column("total", "Total"),
)

TIME_OFF_ASSIGNMENTS: Final = (
    Column("id", "ID"),
    Column("userId", "User"),
    Column("policyId", "Policy"),
    Column("balance", "Balance"),
    Column("accrued", "Accrued"),
    Column("dateRange.start", "Start"),
    Column("dateRange.end", "End"),
)

APPROVALS: Final = (
    Column("approvalRequest.id", "ID"),
    Column("approvalRequest.type", "Type"),
    Column("approvalRequest.status.state", "State"),
    Column("approvalRequest.owner.userName", "Owner"),
    Column("approvalRequest.dateRange.start", "Start"),
    Column("approvalRequest.dateRange.end", "End"),
    Column("trackedTime", "Tracked"),
    Column("pendingTime", "Pending"),
)

APPROVAL_REQUESTS: Final = (
    Column("id", "ID"),
    Column("type", "Type"),
    Column("status.state", "State"),
    Column("owner.userName", "Owner"),
    Column("dateRange.start", "Start"),
    Column("dateRange.end", "End"),
)

EXPENSES: Final = (
    Column("id", "ID"),
    Column("date", "Date"),
    Column("category.name", "Category"),
    Column("project.name", "Project"),
    Column("total", "Total"),
    Column("billable", "Billable"),
    Column("notes", "Notes"),
    Column("fileName", "Receipt"),
)

EXPENSE: Final = (
    Column("id", "ID"),
    Column("date", "Date"),
    Column("categoryId", "Category"),
    Column("projectId", "Project"),
    Column("total", "Total"),
    Column("billable", "Billable"),
    Column("notes", "Notes"),
    Column("fileId", "Receipt ID"),
)

EXPENSE_CATEGORIES: Final = (
    Column("id", "ID"),
    Column("name", "Name"),
    Column("archived", "Archived"),
    Column("unit", "Unit"),
    Column("priceInCents", "Unit price (cents)"),
)
