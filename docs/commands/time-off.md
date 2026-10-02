---
type: reference
title: Time off and approvals
description: Why request decisions look up their policy, how policy updates keep unchanged settings, and which balance changes are deltas that must not be repeated.
tags: [commands, time-off, approvals]
status: stable
---

# Time off and approvals

Time off and approvals are Standard-plan features. On a lower plan Clockify
answers `403`, which the CLI reports with exit code 5. The models follow the
OpenAPI spec and were not checked against a real response; see the SDK's
`docs/sdk/time-off.md`.

## Requests hang off a policy

Clockify has no endpoint that reads one time off request, and every request
route includes its policy ID. `time-off request approve|reject|delete REQUEST`
therefore needs the policy:

- With `--policy`, the CLI uses it, as an ID or an exact name.
- Without it, the CLI lists the workspace's requests and takes the policy of
  the one whose ID matches. A request that the list does not show exits with
  code 6; pass `--policy` then.

## Policy updates keep what you leave out

`PUT .../time-off/policies/{id}` replaces the whole policy and requires every
flag. `time-off policy update` reads the stored policy first and sends it back
with only the options you passed changed, including accrual, negative balance,
automatic time entries, members and groups. `--user` and `--group` replace the
stored list instead of adding to it. A policy's time unit cannot change.

## Balance changes are deltas

- `time-off balance update --value` and `update-assignment --change` add to the
  balance; they do not set it. Negative numbers subtract.
- Clockify does not retry them on a server error, because a repeat would apply
  the change twice. Check the balance with `balance list` before running the
  command again after a failure.
- `balance assign` sets the balance of a new assignment.
- `delete-assignment` needs `--note`, which Clockify records.

## Approvals

- Approval requests have no read endpoint either, so `approve`, `reject` and
  `withdraw` take the request ID shown by `approval list`.
- `withdraw` withdraws your own submission. With `--approval` it withdraws an
  approval you gave.
- The SDK has no resubmit for another user, so `approval resubmit` always acts
  for the signed-in user.
