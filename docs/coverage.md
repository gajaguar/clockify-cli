# Endpoint coverage

Authoritative mapping of every non-deprecated operation in Clockify's
[OpenAPI document](https://docs.clockify.me/openapi.json) to the SDK method
that wraps it and the CLI command that exposes it. "100% coverage" means
every row below is `done`; `make coverage-report` verifies the table against
the live spec so a new upstream endpoint shows up as a missing row.

- **Endpoint** paths omit the `/v1` prefix; deprecated operations are
  excluded (see [ROADMAP.md](ROADMAP.md#deprecated-endpoints)).
- **SDK method** is empty until the method ships in
  [`clockify-sdk`](https://github.com/gajaguar/clockify-sdk); `ws` is a
  `WorkspaceClient`.
- **CLI command** is the proposed command surface; names are provisional
  until the phase starts.
- **Status** tracks the CLI: `planned`, `in-progress`, `done`.

## Workspaces

| Endpoint                                                   | SDK method                  | CLI command                                             | Phase | Status  |
| ---------------------------------------------------------- | --------------------------- | ------------------------------------------------------- | ----- | ------- |
| `GET /workspaces`                                          | `client.workspaces.list()`  | `clockify workspace list`                               | 1     | done    |
| `GET /workspaces/{workspaceId}`                            | `client.workspaces.get(id)` | `clockify workspace get [ID]`                           | 1     | done    |
| `POST /workspaces`                                         |                             | `clockify workspace create NAME`                        | 2     | planned |
| `PUT /workspaces/{workspaceId}/cost-rate`                  |                             | `clockify workspace set-cost-rate AMOUNT`               | 2     | planned |
| `PUT /workspaces/{workspaceId}/hourly-rate`                |                             | `clockify workspace set-billable-rate AMOUNT`           | 2     | planned |
| `POST /workspaces/{workspaceId}/users`                     |                             | `clockify workspace invite EMAIL...`                    | 2     | planned |
| `POST /workspaces/{workspaceId}/limited-users`             |                             | `clockify workspace add-limited-user NAME...`           | 2     | planned |
| `PUT /workspaces/{workspaceId}/users/{userId}`             |                             | `clockify workspace set-user-status USER --status`      | 2     | planned |
| `PUT /workspaces/{workspaceId}/users/{userId}/cost-rate`   |                             | `clockify workspace set-user-cost-rate USER AMOUNT`     | 2     | planned |
| `PUT /workspaces/{workspaceId}/users/{userId}/hourly-rate` |                             | `clockify workspace set-user-billable-rate USER AMOUNT` | 2     | planned |

## Users

| Endpoint                                                                          | SDK method         | CLI command                                | Phase | Status  |
| --------------------------------------------------------------------------------- | ------------------ | ------------------------------------------ | ----- | ------- |
| `GET /user`                                                                       | `client.user.me()` | `clockify user me`                         | 1     | done    |
| `GET /workspaces/{workspaceId}/users`                                             | `ws.users.list()`  | `clockify user list`                       | 1     | done    |
| `POST /file/image`                                                                |                    | `clockify user set-photo FILE`             | 2     | planned |
| `GET /workspaces/{workspaceId}/member-profile/{userId}`                           |                    | `clockify user profile get USER`           | 2     | planned |
| `PATCH /workspaces/{workspaceId}/member-profile/{userId}`                         |                    | `clockify user profile update USER`        | 2     | planned |
| `POST /workspaces/{workspaceId}/users/info`                                       |                    | `clockify user search --status --role ...` | 2     | planned |
| `PUT /workspaces/{workspaceId}/users/{userId}/custom-field/{customFieldId}/value` |                    | `clockify user set-field USER FIELD VALUE` | 2     | planned |
| `GET /workspaces/{workspaceId}/users/{userId}/managers`                           |                    | `clockify user managers USER`              | 2     | planned |
| `POST /workspaces/{workspaceId}/users/{userId}/roles`                             |                    | `clockify user grant-manager USER`         | 2     | planned |
| `DELETE /workspaces/{workspaceId}/users/{userId}/roles`                           |                    | `clockify user revoke-manager USER`        | 2     | planned |

## User groups

| Endpoint                                                                    | SDK method                           | CLI command                             | Phase | Status  |
| --------------------------------------------------------------------------- | ------------------------------------ | --------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/user-groups`                                 | `ws.user_groups.list()`              | `clockify group list`                   | 1     | done    |
| `POST /workspaces/{workspaceId}/user-groups`                                | `ws.user_groups.create(payload)`     | `clockify group create NAME`            | 1     | done    |
| `PUT /workspaces/{workspaceId}/user-groups/{id}`                            | `ws.user_groups.update(id, payload)` | `clockify group update GROUP`           | 1     | done    |
| `DELETE /workspaces/{workspaceId}/user-groups/{id}`                         | `ws.user_groups.delete(id)`          | `clockify group delete GROUP`           | 1     | done    |
| `POST /workspaces/{workspaceId}/user-groups/{userGroupId}/users`            |                                      | `clockify group add-user GROUP USER`    | 2     | planned |
| `DELETE /workspaces/{workspaceId}/user-groups/{userGroupId}/users/{userId}` |                                      | `clockify group remove-user GROUP USER` | 2     | planned |

## Clients

| Endpoint                                        | SDK method                       | CLI command                     | Phase | Status  |
| ----------------------------------------------- | -------------------------------- | ------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/clients`         | `ws.clients.list()`              | `clockify client list`          | 1     | done    |
| `GET /workspaces/{workspaceId}/clients/{id}`    | `ws.clients.get(id)`             | `clockify client get CLIENT`    | 1     | done    |
| `POST /workspaces/{workspaceId}/clients`        | `ws.clients.create(payload)`     | `clockify client create NAME`   | 1     | done    |
| `PUT /workspaces/{workspaceId}/clients/{id}`    | `ws.clients.update(id, payload)` | `clockify client update CLIENT` | 1     | done    |
| `DELETE /workspaces/{workspaceId}/clients/{id}` | `ws.clients.delete(id)`          | `clockify client delete CLIENT` | 1     | done    |

## Projects

| Endpoint                                                                        | SDK method                        | CLI command                                                   | Phase | Status  |
| ------------------------------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/projects`                                        | `ws.projects.list()`              | `clockify project list`                                       | 1     | done    |
| `GET /workspaces/{workspaceId}/projects/{projectId}`                            | `ws.projects.get(id)`             | `clockify project get PROJECT`                                | 1     | done    |
| `POST /workspaces/{workspaceId}/projects`                                       | `ws.projects.create(payload)`     | `clockify project create NAME`                                | 1     | done    |
| `PUT /workspaces/{workspaceId}/projects/{projectId}`                            | `ws.projects.update(id, payload)` | `clockify project update PROJECT`                             | 1     | done    |
| `DELETE /workspaces/{workspaceId}/projects/{projectId}`                         | `ws.projects.delete(id)`          | `clockify project delete PROJECT`                             | 1     | done    |
| `POST /workspaces/{workspaceId}/projects/from-template`                         |                                   | `clockify project create NAME --from-template TEMPLATE`       | 2     | planned |
| `PATCH /workspaces/{workspaceId}/projects/{projectId}/estimate`                 |                                   | `clockify project set-estimate PROJECT`                       | 2     | planned |
| `PATCH /workspaces/{workspaceId}/projects/{projectId}/memberships`              |                                   | `clockify project members set PROJECT`                        | 2     | planned |
| `POST /workspaces/{workspaceId}/projects/{projectId}/memberships`               |                                   | `clockify project members add/remove PROJECT USER...`         | 2     | planned |
| `PATCH /workspaces/{workspaceId}/projects/{projectId}/template`                 |                                   | `clockify project set-template PROJECT --on/--off`            | 2     | planned |
| `PUT /workspaces/{workspaceId}/projects/{projectId}/users/{userId}/cost-rate`   |                                   | `clockify project set-user-cost-rate PROJECT USER AMOUNT`     | 2     | planned |
| `PUT /workspaces/{workspaceId}/projects/{projectId}/users/{userId}/hourly-rate` |                                   | `clockify project set-user-billable-rate PROJECT USER AMOUNT` | 2     | planned |

## Tasks

| Endpoint                                                                    | SDK method                                 | CLI command                                              | Phase | Status  |
| --------------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/projects/{projectId}/tasks`                  | `ws.tasks.list(project_id)`                | `clockify task list -P PROJECT`                          | 1     | done    |
| `GET /workspaces/{workspaceId}/projects/{projectId}/tasks/{taskId}`         | `ws.tasks.get(project_id, id)`             | `clockify task get -P PROJECT TASK`                      | 1     | done    |
| `POST /workspaces/{workspaceId}/projects/{projectId}/tasks`                 | `ws.tasks.create(project_id, payload)`     | `clockify task create -P PROJECT NAME`                   | 1     | done    |
| `PUT /workspaces/{workspaceId}/projects/{projectId}/tasks/{taskId}`         | `ws.tasks.update(project_id, id, payload)` | `clockify task update -P PROJECT TASK`                   | 1     | done    |
| `DELETE /workspaces/{workspaceId}/projects/{projectId}/tasks/{taskId}`      | `ws.tasks.delete(project_id, id)`          | `clockify task delete -P PROJECT TASK`                   | 1     | done    |
| `PUT /workspaces/{workspaceId}/projects/{projectId}/tasks/{id}/cost-rate`   |                                            | `clockify task set-cost-rate -P PROJECT TASK AMOUNT`     | 2     | planned |
| `PUT /workspaces/{workspaceId}/projects/{projectId}/tasks/{id}/hourly-rate` |                                            | `clockify task set-billable-rate -P PROJECT TASK AMOUNT` | 2     | planned |

## Tags

| Endpoint                                     | SDK method                    | CLI command                | Phase | Status  |
| -------------------------------------------- | ----------------------------- | -------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/tags`         | `ws.tags.list()`              | `clockify tag list`        | 1     | done    |
| `GET /workspaces/{workspaceId}/tags/{id}`    | `ws.tags.get(id)`             | `clockify tag get TAG`     | 1     | done    |
| `POST /workspaces/{workspaceId}/tags`        | `ws.tags.create(payload)`     | `clockify tag create NAME` | 1     | done    |
| `PUT /workspaces/{workspaceId}/tags/{id}`    | `ws.tags.update(id, payload)` | `clockify tag update TAG`  | 1     | done    |
| `DELETE /workspaces/{workspaceId}/tags/{id}` | `ws.tags.delete(id)`          | `clockify tag delete TAG`  | 1     | done    |

## Custom fields

| Endpoint                                                                              | SDK method                             | CLI command                                     | Phase | Status  |
| ------------------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/custom-fields`                                         | `ws.custom_fields.list()`              | `clockify custom-field list`                    | 1     | done    |
| `POST /workspaces/{workspaceId}/custom-fields`                                        | `ws.custom_fields.create(payload)`     | `clockify custom-field create NAME`             | 1     | done    |
| `PUT /workspaces/{workspaceId}/custom-fields/{customFieldId}`                         | `ws.custom_fields.update(id, payload)` | `clockify custom-field update FIELD`            | 1     | done    |
| `DELETE /workspaces/{workspaceId}/custom-fields/{customFieldId}`                      | `ws.custom_fields.delete(id)`          | `clockify custom-field delete FIELD`            | 1     | done    |
| `GET /workspaces/{workspaceId}/projects/{projectId}/custom-fields`                    |                                        | `clockify custom-field list -P PROJECT`         | 2     | planned |
| `PATCH /workspaces/{workspaceId}/projects/{projectId}/custom-fields/{customFieldId}`  |                                        | `clockify custom-field update FIELD -P PROJECT` | 2     | planned |
| `DELETE /workspaces/{workspaceId}/projects/{projectId}/custom-fields/{customFieldId}` |                                        | `clockify custom-field remove FIELD -P PROJECT` | 2     | planned |

## Time entries

| Endpoint                                                                   | SDK method                                        | CLI command                                          | Phase | Status  |
| -------------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/user/{userId}/time-entries`                 | `ws.time_entries.list(user_id, entry_filter=...)` | `clockify entry list`                                | 1     | done    |
| `GET /workspaces/{workspaceId}/time-entries/{id}`                          | `ws.time_entries.get(id)`                         | `clockify entry get ENTRY`                           | 1     | done    |
| `POST /workspaces/{workspaceId}/time-entries`                              | `ws.time_entries.create(payload)`                 | `clockify entry create / clockify log`               | 1     | done    |
| `POST /workspaces/{workspaceId}/user/{userId}/time-entries`                | `ws.time_entries.start(user_id, payload)`         | `clockify start / clockify entry create --user USER` | 1     | done    |
| `PUT /workspaces/{workspaceId}/time-entries/{id}`                          | `ws.time_entries.update(id, payload)`             | `clockify entry update ENTRY`                        | 1     | done    |
| `PATCH /workspaces/{workspaceId}/user/{userId}/time-entries`               | `ws.time_entries.stop(user_id, end=None)`         | `clockify stop`                                      | 1     | done    |
| `DELETE /workspaces/{workspaceId}/time-entries/{id}`                       | `ws.time_entries.delete(id)`                      | `clockify entry delete ENTRY`                        | 1     | done    |
| `POST /workspaces/{workspaceId}/time-entries/batch`                        |                                                   | `clockify entry get ENTRY...`                        | 2     | planned |
| `PATCH /workspaces/{workspaceId}/time-entries/invoiced`                    |                                                   | `clockify entry mark-invoiced ENTRY...`              | 2     | planned |
| `GET /workspaces/{workspaceId}/time-entries/status/in-progress`            |                                                   | `clockify entry running --all-users`                 | 2     | planned |
| `DELETE /workspaces/{workspaceId}/user/{userId}/time-entries`              |                                                   | `clockify entry delete ENTRY... --user USER`         | 2     | planned |
| `PUT /workspaces/{workspaceId}/user/{userId}/time-entries`                 |                                                   | `clockify entry bulk-update --user USER`             | 2     | planned |
| `POST /workspaces/{workspaceId}/user/{userId}/time-entries/{id}/duplicate` |                                                   | `clockify entry duplicate ENTRY / clockify continue` | 2     | planned |

## Reports

| Endpoint                                                   | SDK method | CLI command                              | Phase | Status  |
| ---------------------------------------------------------- | ---------- | ---------------------------------------- | ----- | ------- |
| `POST /workspaces/{workspaceId}/reports/detailed`          |            | `clockify report detailed`               | 3     | planned |
| `POST /workspaces/{workspaceId}/reports/summary`           |            | `clockify report summary`                | 3     | planned |
| `POST /workspaces/{workspaceId}/reports/weekly`            |            | `clockify report weekly`                 | 3     | planned |
| `POST /workspaces/{workspaceId}/reports/attendance`        |            | `clockify report attendance`             | 3     | planned |
| `POST /workspaces/{workspaceId}/reports/expenses/detailed` |            | `clockify report expenses`               | 3     | planned |
| `POST /workspaces/{workspaceId}/audit-log`                 |            | `clockify report audit-log`              | 3     | planned |
| `GET /shared-reports/{id}`                                 |            | `clockify shared-report generate REPORT` | 3     | planned |
| `GET /workspaces/{workspaceId}/shared-reports`             |            | `clockify shared-report list`            | 3     | planned |
| `POST /workspaces/{workspaceId}/shared-reports`            |            | `clockify shared-report create NAME`     | 3     | planned |
| `PUT /workspaces/{workspaceId}/shared-reports/{id}`        |            | `clockify shared-report update REPORT`   | 3     | planned |
| `DELETE /workspaces/{workspaceId}/shared-reports/{id}`     |            | `clockify shared-report delete REPORT`   | 3     | planned |

## Time off

| Endpoint                                                                                                             | SDK method | CLI command                                                   | Phase | Status  |
| -------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/time-off/policies`                                                                    |            | `clockify time-off policy list`                               | 4     | planned |
| `GET /workspaces/{workspaceId}/time-off/policies/{id}`                                                               |            | `clockify time-off policy get POLICY`                         | 4     | planned |
| `POST /workspaces/{workspaceId}/time-off/policies`                                                                   |            | `clockify time-off policy create NAME`                        | 4     | planned |
| `PUT /workspaces/{workspaceId}/time-off/policies/{id}`                                                               |            | `clockify time-off policy update POLICY`                      | 4     | planned |
| `PATCH /workspaces/{workspaceId}/time-off/policies/{id}`                                                             |            | `clockify time-off policy archive/restore POLICY`             | 4     | planned |
| `DELETE /workspaces/{workspaceId}/time-off/policies/{id}`                                                            |            | `clockify time-off policy delete POLICY`                      | 4     | planned |
| `POST /workspaces/{workspaceId}/time-off/requests`                                                                   |            | `clockify time-off request list`                              | 4     | planned |
| `POST /workspaces/{workspaceId}/time-off/policies/{policyId}/requests`                                               |            | `clockify time-off request create -P POLICY`                  | 4     | planned |
| `POST /workspaces/{workspaceId}/time-off/policies/{policyId}/users/{userId}/requests`                                |            | `clockify time-off request create -P POLICY --user USER`      | 4     | planned |
| `PATCH /workspaces/{workspaceId}/time-off/policies/{policyId}/requests/{requestId}`                                  |            | `clockify time-off request approve/reject REQUEST`            | 4     | planned |
| `DELETE /workspaces/{workspaceId}/time-off/policies/{policyId}/requests/{requestId}`                                 |            | `clockify time-off request delete REQUEST`                    | 4     | planned |
| `GET /workspaces/{workspaceId}/time-off/balance/policy/{policyId}`                                                   |            | `clockify time-off balance list -P POLICY`                    | 4     | planned |
| `GET /workspaces/{workspaceId}/time-off/balance/user/{userId}`                                                       |            | `clockify time-off balance list --user USER`                  | 4     | planned |
| `PATCH /workspaces/{workspaceId}/time-off/balance/policy/{policyId}`                                                 |            | `clockify time-off balance update -P POLICY`                  | 4     | planned |
| `POST /workspaces/{workspaceId}/time-off/balance/assignment`                                                         |            | `clockify time-off balance assign`                            | 4     | planned |
| `GET /workspaces/{workspaceId}/time-off/balance/assignment/user/{userId}/policy/{policyId}`                          |            | `clockify time-off balance assignments -P POLICY --user USER` | 4     | planned |
| `PUT /workspaces/{workspaceId}/time-off/balance/assignment/{balanceAssignmentId}/user/{userId}/policy/{policyId}`    |            | `clockify time-off balance update-assignment ASSIGNMENT`      | 4     | planned |
| `DELETE /workspaces/{workspaceId}/time-off/balance/assignment/{balanceAssignmentId}/user/{userId}/policy/{policyId}` |            | `clockify time-off balance delete-assignment ASSIGNMENT`      | 4     | planned |

## Holidays

| Endpoint                                                | SDK method | CLI command                         | Phase | Status  |
| ------------------------------------------------------- | ---------- | ----------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/holidays`                |            | `clockify holiday list`             | 4     | planned |
| `GET /workspaces/{workspaceId}/holidays/in-period`      |            | `clockify holiday list --from --to` | 4     | planned |
| `POST /workspaces/{workspaceId}/holidays`               |            | `clockify holiday create NAME`      | 4     | planned |
| `PUT /workspaces/{workspaceId}/holidays/{holidayId}`    |            | `clockify holiday update HOLIDAY`   | 4     | planned |
| `DELETE /workspaces/{workspaceId}/holidays/{holidayId}` |            | `clockify holiday delete HOLIDAY`   | 4     | planned |

## Approvals

| Endpoint                                                                                        | SDK method | CLI command                                         | Phase | Status  |
| ----------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/approval-requests`                                               |            | `clockify approval list`                            | 4     | planned |
| `POST /workspaces/{workspaceId}/approval-requests/{type}`                                       |            | `clockify approval submit --type`                   | 4     | planned |
| `POST /workspaces/{workspaceId}/approval-requests/users/{userId}/{type}`                        |            | `clockify approval submit --type --user USER`       | 4     | planned |
| `POST /workspaces/{workspaceId}/approval-requests/resubmit-entries-for-approval`                |            | `clockify approval resubmit`                        | 4     | planned |
| `POST /workspaces/{workspaceId}/approval-requests/users/{userId}/resubmit-entries-for-approval` |            | `clockify approval resubmit --user USER`            | 4     | planned |
| `PATCH /workspaces/{workspaceId}/approval-requests/{approvalRequestId}`                         |            | `clockify approval approve/reject/withdraw REQUEST` | 4     | planned |

## Expenses

| Endpoint                                                                  | SDK method | CLI command                                          | Phase | Status  |
| ------------------------------------------------------------------------- | ---------- | ---------------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/expenses`                                  |            | `clockify expense list`                              | 5     | planned |
| `GET /workspaces/{workspaceId}/expenses/{expenseId}`                      |            | `clockify expense get EXPENSE`                       | 5     | planned |
| `POST /workspaces/{workspaceId}/expenses`                                 |            | `clockify expense create --receipt FILE`             | 5     | planned |
| `PUT /workspaces/{workspaceId}/expenses/{expenseId}`                      |            | `clockify expense update EXPENSE`                    | 5     | planned |
| `DELETE /workspaces/{workspaceId}/expenses/{expenseId}`                   |            | `clockify expense delete EXPENSE`                    | 5     | planned |
| `GET /workspaces/{workspaceId}/expenses/{expenseId}/files/{fileId}`       |            | `clockify expense receipt EXPENSE --save FILE`       | 5     | planned |
| `GET /workspaces/{workspaceId}/expenses/categories`                       |            | `clockify expense category list`                     | 5     | planned |
| `POST /workspaces/{workspaceId}/expenses/categories`                      |            | `clockify expense category create NAME`              | 5     | planned |
| `PUT /workspaces/{workspaceId}/expenses/categories/{categoryId}`          |            | `clockify expense category update CATEGORY`          | 5     | planned |
| `PATCH /workspaces/{workspaceId}/expenses/categories/{categoryId}/status` |            | `clockify expense category archive/restore CATEGORY` | 5     | planned |
| `DELETE /workspaces/{workspaceId}/expenses/categories/{categoryId}`       |            | `clockify expense category delete CATEGORY`          | 5     | planned |

## Invoices

| Endpoint                                                                     | SDK method | CLI command                                        | Phase | Status  |
| ---------------------------------------------------------------------------- | ---------- | -------------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/invoices`                                     |            | `clockify invoice list`                            | 5     | planned |
| `POST /workspaces/{workspaceId}/invoices/info`                               |            | `clockify invoice list --status --client ...`      | 5     | planned |
| `GET /workspaces/{workspaceId}/invoices/{invoiceId}`                         |            | `clockify invoice get INVOICE`                     | 5     | planned |
| `POST /workspaces/{workspaceId}/invoices`                                    |            | `clockify invoice create --client CLIENT`          | 5     | planned |
| `PUT /workspaces/{workspaceId}/invoices/{invoiceId}`                         |            | `clockify invoice update INVOICE`                  | 5     | planned |
| `DELETE /workspaces/{workspaceId}/invoices/{invoiceId}`                      |            | `clockify invoice delete INVOICE`                  | 5     | planned |
| `POST /workspaces/{workspaceId}/invoices/{invoiceId}/duplicate`              |            | `clockify invoice duplicate INVOICE`               | 5     | planned |
| `GET /workspaces/{workspaceId}/invoices/{invoiceId}/export`                  |            | `clockify invoice export INVOICE --save FILE`      | 5     | planned |
| `PATCH /workspaces/{workspaceId}/invoices/{invoiceId}/status`                |            | `clockify invoice set-status INVOICE STATUS`       | 5     | planned |
| `POST /workspaces/{workspaceId}/invoices/{invoiceId}/items`                  |            | `clockify invoice item add INVOICE`                | 5     | planned |
| `POST /workspaces/{workspaceId}/invoices/{invoiceId}/items/import`           |            | `clockify invoice item import INVOICE --from --to` | 5     | planned |
| `DELETE /workspaces/{workspaceId}/invoices/{invoiceId}/items/{order}`        |            | `clockify invoice item delete INVOICE ORDER`       | 5     | planned |
| `GET /workspaces/{workspaceId}/invoices/{invoiceId}/payments`                |            | `clockify invoice payment list INVOICE`            | 5     | planned |
| `POST /workspaces/{workspaceId}/invoices/{invoiceId}/payments`               |            | `clockify invoice payment add INVOICE AMOUNT`      | 5     | planned |
| `DELETE /workspaces/{workspaceId}/invoices/{invoiceId}/payments/{paymentId}` |            | `clockify invoice payment delete INVOICE PAYMENT`  | 5     | planned |
| `GET /workspaces/{workspaceId}/invoices/settings`                            |            | `clockify invoice settings get`                    | 5     | planned |
| `PUT /workspaces/{workspaceId}/invoices/settings`                            |            | `clockify invoice settings update`                 | 5     | planned |

## Scheduling

| Endpoint                                                                           | SDK method | CLI command                                   | Phase | Status  |
| ---------------------------------------------------------------------------------- | ---------- | --------------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/scheduling/assignments/all`                         |            | `clockify schedule list`                      | 6     | planned |
| `POST /workspaces/{workspaceId}/scheduling/assignments/recurring`                  |            | `clockify schedule create`                    | 6     | planned |
| `PATCH /workspaces/{workspaceId}/scheduling/assignments/recurring/{assignmentId}`  |            | `clockify schedule update ASSIGNMENT`         | 6     | planned |
| `DELETE /workspaces/{workspaceId}/scheduling/assignments/recurring/{assignmentId}` |            | `clockify schedule delete ASSIGNMENT`         | 6     | planned |
| `PUT /workspaces/{workspaceId}/scheduling/assignments/series/{assignmentId}`       |            | `clockify schedule set-recurrence ASSIGNMENT` | 6     | planned |
| `POST /workspaces/{workspaceId}/scheduling/assignments/{assignmentId}/copy`        |            | `clockify schedule copy ASSIGNMENT`           | 6     | planned |
| `PUT /workspaces/{workspaceId}/scheduling/assignments/publish`                     |            | `clockify schedule publish`                   | 6     | planned |
| `POST /workspaces/{workspaceId}/scheduling/assignments/projects/totals`            |            | `clockify schedule totals --by project`       | 6     | planned |
| `GET /workspaces/{workspaceId}/scheduling/assignments/projects/totals/{projectId}` |            | `clockify schedule totals -P PROJECT`         | 6     | planned |
| `POST /workspaces/{workspaceId}/scheduling/assignments/user-filter/totals`         |            | `clockify schedule capacity`                  | 6     | planned |
| `GET /workspaces/{workspaceId}/scheduling/assignments/users/{userId}/totals`       |            | `clockify schedule capacity --user USER`      | 6     | planned |

## Webhooks

| Endpoint                                                      | SDK method | CLI command                             | Phase | Status  |
| ------------------------------------------------------------- | ---------- | --------------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/webhooks`                      |            | `clockify webhook list`                 | 6     | planned |
| `GET /workspaces/{workspaceId}/addons/{addonId}/webhooks`     |            | `clockify webhook list --addon ADDON`   | 6     | planned |
| `GET /workspaces/{workspaceId}/webhooks/{webhookId}`          |            | `clockify webhook get WEBHOOK`          | 6     | planned |
| `POST /workspaces/{workspaceId}/webhooks`                     |            | `clockify webhook create URL --event`   | 6     | planned |
| `PUT /workspaces/{workspaceId}/webhooks/{webhookId}`          |            | `clockify webhook update WEBHOOK`       | 6     | planned |
| `DELETE /workspaces/{workspaceId}/webhooks/{webhookId}`       |            | `clockify webhook delete WEBHOOK`       | 6     | planned |
| `PATCH /workspaces/{workspaceId}/webhooks/{webhookId}/token`  |            | `clockify webhook rotate-token WEBHOOK` | 6     | planned |
| `POST /workspaces/{workspaceId}/webhooks/{webhookId}/logs`    |            | `clockify webhook logs WEBHOOK`         | 6     | planned |
| `GET /workspaces/{workspaceId}/webhooks/{webhookId}/statuses` |            | `clockify webhook statuses WEBHOOK`     | 6     | planned |

## Entity changes (experimental)

| Endpoint                                         | SDK method | CLI command                        | Phase | Status  |
| ------------------------------------------------ | ---------- | ---------------------------------- | ----- | ------- |
| `GET /workspaces/{workspaceId}/entities/created` |            | `clockify changes created --since` | 6     | planned |
| `GET /workspaces/{workspaceId}/entities/updated` |            | `clockify changes updated --since` | 6     | planned |
| `GET /workspaces/{workspaceId}/entities/deleted` |            | `clockify changes deleted --since` | 6     | planned |
