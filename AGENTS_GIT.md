# AGENTS_GIT.md

Git conventions for skills-comm. Applies to humans and agents alike.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(optional-scope): tagline
```

- **Messages are terse.** One line is the norm. Add a body only for extensive changes
  that genuinely need explanation (rationale, trade-offs, migration notes).
- **Scope** is usually the contribution directory or skill, e.g. `feat(datalad-cli): ...`,
  `fix(brain-extraction): ...`, `docs(readme): ...`.
- Use the imperative mood in the tagline ("add", not "added"/"adds").

### Types

| Type | Use for |
|---|---|
| `feat` | a new skill, plugin, or capability |
| `fix` | correcting a broken skill (bad flags, wrong order, failing recipe) |
| `docs` | README, references, frontmatter descriptions, this kind of file |
| `refactor` | restructuring a skill without changing its behavior |
| `chore` | repo maintenance (gitignore, file moves, cleanup) |
| `test` | adding or updating test/evaluation evidence |

Examples:

```
feat(nipoppy-cli): add IDP extraction skill
fix(brain-extraction): pin fsl module to 6.0.7.22
docs(contributing): clarify issue-first requirement
chore: remove .ipynb_checkpoints and add .gitignore
```

## Branches

- Never commit directly to `main`. Branch first.
- Name branches `type/short-slug`, e.g. `feat/qsiprep-skill`, `fix/synthstrip-paths`.

## Pull requests

- Commit and push only when the human asks.
- PR titles follow the same Conventional Commits format as commits.
- See [AGENTS_CONTRIBUTING.md](AGENTS_CONTRIBUTING.md) for the full PR body structure and
  the contribution checklist.
