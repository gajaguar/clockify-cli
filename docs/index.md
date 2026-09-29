---
okf_version: "0.2"
---

# Documentation

This is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
(OKF) bundle: one Markdown concept per file, each with YAML frontmatter, laid
out under this directory.

## Reference

* [Conventions](conventions/index.md) - commit and branch naming, and how
  they're enforced.
* [Toolchain](toolchain/index.md) - which layer (mise or an ecosystem
  package manager) installs which tool, and why.

See [`log.md`](log.md) for the bundle's change history.

## Project

* [Architecture](ARCHITECTURE.md) - the technical specification: stack,
  layering, design patterns, authentication and how to add a command.
* [Roadmap](ROADMAP.md) - the phased delivery plan.
* [Endpoint coverage](coverage.md) - each Clockify operation mapped to its
  SDK method and CLI command.

## Python

* [Python](python/index.md) - the interpreter source and the
  `pyproject.toml` settings left out on purpose.
