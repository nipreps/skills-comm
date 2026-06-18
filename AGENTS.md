# AGENTS.md

Operating guide for LLM agents working in **skills-comm**, a community collection of
neuroimaging skills. Start with the [README](README.md) for what the project is and how
it's organized.

This file is intentionally minimal. Read the relevant sibling file for the task at hand:

- **[README.md](README.md)** — project overview, repo layout, skill anatomy.
- **[CLAUDE.md](CLAUDE.md)** — architecture and conventions for working *inside* this repo
  (where things live, how a skill is structured, how to validate one).
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — the human-facing procedure to submit a skill
  (issue first, structure, testing, review).
- **[AGENTS_CONTRIBUTING.md](AGENTS_CONTRIBUTING.md)** — how an agent should prepare a
  contribution: PR title/body structure, documentation requirements, self-checks.
- **[AGENTS_GIT.md](AGENTS_GIT.md)** — commit, branch, and PR conventions (conventional
  commits, terse messages).

When editing or authoring a *skill*, also read that skill's own `SKILL.md` and any
`AGENTS.md` it ships — skills target the **Neurodesk + Lmod + SLURM** environment and
carry their own hard rules (e.g. never run neuroimaging tools directly; submit via SLURM
with explicitly versioned `module load`).
