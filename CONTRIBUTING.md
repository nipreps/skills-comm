# Contributing to skills-comm

Thanks for helping operationalize neuroimaging tools for LLM agents. This guide is the
procedure for **humans**. If an agent is preparing the contribution on your behalf, point
it at [AGENTS_CONTRIBUTING.md](AGENTS_CONTRIBUTING.md) and [AGENTS_GIT.md](AGENTS_GIT.md)
as well.

## 1. Open an issue first

**Every new skill starts with an issue.** Before writing code, open an issue that
describes:

- **The tool/task** you want to operationalize (e.g. "QSIPrep diffusion preprocessing").
- **The trigger** — what a user would say that should activate the skill.
- **The environment** it targets (Neurodesk + Lmod + SLURM is the default; note any
  deviation).
- **Why a skill helps** — what an agent gets wrong without it.

This lets maintainers and other contributors flag overlap with existing skills, agree on
naming, and avoid duplicated effort. Wait for a maintainer to acknowledge the issue before
investing heavily. Reference the issue number in your PR.

## 2. Decide the packaging

A contribution is one directory under [`plugins/`](plugins/). Two forms are accepted:

- **Full plugin** (preferred) — includes a `.claude-plugin/plugin.json` manifest listing
  its skills, plus a `README.md`. Installable via `claude plugin install`. See
  `plugins/datalad-cli/` and `plugins/nipoppy-cli/` as models.
- **Bare skill collection** — one or more `SKILL.md` directories without a manifest. Fine
  for a first or small contribution. See `plugins/bcmcpher/` and `plugins/kodibaga/`.

Pick a clear, lowercase, hyphenated directory name (the tool or domain, e.g.
`qsiprep-cli`). Don't collide with an existing directory.

## 3. Structure your skill

Each skill is a directory with a `SKILL.md`:

```
plugins/<your-contribution>/
└── <skill-name>/
    ├── SKILL.md            # frontmatter + procedure
    └── references/         # optional, load-on-demand detail
```

`SKILL.md` frontmatter must include:

```yaml
---
name: skill-name                 # matches the directory, lowercase-hyphenated
description: >                   # the trigger — list the phrases/intents that activate it
  One or two sentences on what it does, followed by the verbs and phrases that
  should invoke it.
---
```

Writing guidance:

- **Body is an imperative procedure, not a tutorial.** Number the steps; state hard rules
  in a "Constraints" section.
- **Encode reproducibility.** Pin tool versions (`module load fsl/6.0.7.22`, not `fsl`),
  prefer BIDS layouts, and record provenance (DataLad) where it fits.
- **Respect the environment rules.** Never run heavy neuroimaging tools directly — write a
  script and submit via SLURM; discover tools with `module spider` before using them.
- **Keep `SKILL.md` lean.** Push long tool references, comparison tables, and QC criteria
  into `references/*.md` so they load only when needed.
- Study [`skill-iterations/`](skill-iterations/) — it shows a skill maturing from a rough
  draft to a hardened version, and the kinds of fixes reviewers look for.

If you ship a full plugin, add/extend `.claude-plugin/plugin.json` (name, description,
version, keywords, the `skills` list) and a `README.md` documenting the skills and any
slash commands.

## 4. Test it — manual run with evidence

There is no CI test harness yet, so **you must demonstrate the skill works**:

1. Run the skill end-to-end in its target environment (e.g. Neurodesk) on a real or
   representative input.
2. Confirm it triggers from the intended phrasing, follows its own steps, and produces the
   expected output (including any QC artifact).
3. **Paste the evidence into the PR**: the invocation, the key agent/tool output, and a
   note on the environment and tool versions used. A trimmed transcript is fine; redact
   anything sensitive.

A PR without execution evidence will not be merged.

## 5. Open the pull request

- Branch off `main` (`type/short-slug`); don't push to `main` directly.
- Use a Conventional Commits title (see [AGENTS_GIT.md](AGENTS_GIT.md)), e.g.
  `feat(qsiprep-cli): add diffusion preprocessing skill`.
- In the PR body: link the issue (`Closes #NN`), summarize the skill and its trigger, and
  include the **test evidence** from step 4.
- Keep commits terse and conventional.

## 6. Review

Maintainers review for: correct and reproducible tool usage, a precise `description`
trigger, lean `SKILL.md` with detail pushed to `references/`, adherence to environment
rules (versioned modules, SLURM, no direct heavy execution), and present test evidence.
Expect iteration — see `skill-iterations/` for the kinds of refinements that are normal.

## License

By contributing you agree your contribution is licensed under the repository's
[Apache License 2.0](LICENSE).
