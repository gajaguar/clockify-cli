# Conventions

## README structure

A README is written for a developer who needs to get productive, not as a
table of contents to fill in. Every project built from this template
follows the same shape, but the sections in the middle are whatever *this*
project actually has — don't copy section names from another project's
README if they don't apply here:

1. **Title**, then a badge row: license and topics (generate the topics
   badge from the repo's actual GitHub topics — `gh repo edit --add-topic`
   — rather than hand-picking tags that can drift out of sync), then a
   one-line description.
2. **`## Requirements`** — what has to exist before anything else works.
3. **`## Usage`** — the smallest command sequence that gets something done.
4. Whatever reference sections this project's own components or decisions
   warrant, cross-linked with anchors (`[Containers](#containers)`) rather
   than repeated prose, and tables for anything enumerable.
5. **`## Platform notes`** — non-obvious behavior forced by the underlying
   platform (GitHub, the OS, a provider), not by this project's own design.
6. **`## Open items`** — known gaps or unverified assumptions, stated
   plainly. Omit the section rather than write "none" — an absent section
   already says that.

Skip a section (4, 5, or 6) if the project genuinely has nothing to put in
it; don't pad it with filler to preserve the shape.

## Command convention: `check` vs `fix`

Targets are split by whether they mutate files:

| Umbrella            | Behavior                                                             |
| ------------------- | -------------------------------------------------------------------- |
| `check` (read-only) | Reports problems, exits non-zero, never writes. This is the CI gate. |
| `fix` (writable)    | Mutates files in place.                                              |

Each language branch appends its own targets to `check`/`fix` (and to
`install`/`test`) via `mk/*.mk` — see
[`adding-a-language.md`](adding-a-language.md).

## Scoping with `FILES=`

Most targets accept `FILES="..."` to limit scope to specific paths or globs,
e.g. `make md-lint FILES="README.md"`.

## Commits and branches

- Commit messages follow
  [Conventional Commits](https://www.conventionalcommits.org/); branch names
  follow [Conventional Branch](https://conventional-branch.github.io/) — see
  `AGENTS.md`'s "Commits and branches" section for the normative form of
  both.
- `main` carries anything language-agnostic; a language branch changes its
  own files freely but only *appends* to a file it shares with `main`
  (never edits existing lines), so `git merge main` never conflicts with it.
