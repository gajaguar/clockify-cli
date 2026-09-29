---
type: procedure
title: Releasing to PyPI
description: A GitHub release whose tag matches project.version triggers the publish workflow, which uploads through PyPI Trusted Publishing.
tags: [toolchain, release]
status: stable
---

# Releasing to PyPI

`.github/workflows/publish.yml` builds the sdist and wheel with `make build`
and uploads them with Trusted Publishing, so no PyPI token is stored. The
upload job runs in the `pypi` GitHub environment, which is the environment
name the PyPI publisher must be configured with.

To release:

1. Set `project.version` in `pyproject.toml` and `version` in
   `.claude-plugin/plugin.json`, and merge that change to `main`. A test fails
   when the two differ.
2. Create a GitHub release whose tag is `v<version>`, for example `v0.2.0`.
3. Publishing the release runs the workflow. It fails before building when the
   tag and `project.version` differ.

The workflow can also be started by hand with `workflow_dispatch`, which skips
the tag check.

PyPI never accepts the same version twice and a deleted version cannot be
reused, so check `make build` and the install of the wheel in a clean
environment before tagging.
