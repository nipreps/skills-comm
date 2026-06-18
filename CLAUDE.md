# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A community collection of **Agent Skills** that teach LLM agents to drive neuroimaging
tools correctly and reproducibly. There is no application to build, compile, or run — the
"source" is Markdown (`SKILL.md` + `references/`) and JSON manifests. Value lives in the
*procedures and constraints* the skills encode, so changes are judged on operational
correctness, not code that passes a test runner.

For project conventions, read the docs hub: [AGENTS.md](AGENTS.md) →
[CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS_CONTRIBUTING.md](AGENTS_CONTRIBUTING.md),
[AGENTS_GIT.md](AGENTS_GIT.md). This file covers the *architecture* you need to be
productive.

## Architecture

**Contributions live under `plugins/<name>/`**, in one of two forms — both valid:

- **Full plugin**: a `.claude-plugin/plugin.json` manifest + `README.md` + skills
  (`plugins/datalad-cli`, `plugins/nipoppy-cli`). The manifest's `skills` array lists each
  skill by relative path; `datalad-cli` also wires a `Stop` hook via `hooks/hooks.json`.
- **Bare skill collection**: `SKILL.md` directories with no manifest
  (`plugins/bcmcpher`, `plugins/kodibaga`).

**A skill is progressive disclosure.** Three layers, loaded only as far as needed:

1. `SKILL.md` **frontmatter `description`** — the *trigger*. The agent matches user intent
   against the phrases listed here to decide whether to load the skill at all. A vague
   description is a broken skill.
2. `SKILL.md` **body** — a terse, numbered, imperative procedure plus a **Constraints**
   section of hard rules. This is loaded when the skill activates.
3. `references/*.md` — long material (tool flag tables, QC criteria, tool comparisons)
   loaded on demand from within the procedure. Keeping the body lean and pushing detail
   here is the central design pattern; see `plugins/bcmcpher/brain-extraction/` (a short
   `SKILL.md` that pulls per-tool detail from `references/{fsl-bet,ants-brain-extraction,
   synthstrip,...}.md`).

**Shared environment contract.** Skills target **Neurodesk + Lmod modules + SLURM**, and
they encode the same non-negotiable rules (see any `SKILL.md` "Constraints" section and the
`AGENTS.md` files under `skill-iterations/`):

- Never run heavy neuroimaging tools directly — write a script and submit via `sbatch`.
- Discover tools with `module spider`/`module avail`; pin versions in `module load`
  (`fsl/6.0.7.22`, never `fsl`).
- Prefer BIDS layouts; capture provenance with DataLad where it fits.
- Cross-skill handoff is by convention: e.g. `brain-extraction` finishes by invoking
  `brain-extraction-qc` with standardized `_desc-brain_mask.nii.gz` output names, and some
  skills scaffold a Nipoppy pipeline rather than a standalone script when the input is in a
  Nipoppy dataset.

**`skill-iterations/` is a worked example, not a contribution.** It captures one skill
(`brain-extraction`) across six refinement stages (`1_fix_yaml_syntax` →
`6_improve_qc`). Diff adjacent stages to see what hardening a skill looks like: fixing
frontmatter YAML, removing "Claude-isms", generalizing across tools, and strengthening QC.

## Commands

No build/lint/test toolchain. The useful operations are:

```bash
# Load a plugin for one session to test it
claude --plugin-dir ./plugins/<name>

# Install a plugin permanently
claude plugin install ./plugins/<name>

# Validate a plugin manifest is well-formed JSON and inspect its skills
jq . plugins/<name>/.claude-plugin/plugin.json

# List every skill in the repo
find plugins -name SKILL.md

# Check a SKILL.md's frontmatter trigger
sed -n '/^---$/,/^---$/p' plugins/<name>/<skill>/SKILL.md
```

For nipoppy-authored pipelines a skill may instruct `nipoppy pipeline validate`/`install`;
that is a skill *step*, not a repo command.

## When changing things

- Editing a skill: read its `SKILL.md` and its `references/` first; preserve the
  Constraints and the environment rules above. Keep the body lean — new detail goes in
  `references/`.
- Adding a contribution: it goes under `plugins/<name>/` and requires a prior, acknowledged
  issue plus manual-run test evidence in the PR — see [CONTRIBUTING.md](CONTRIBUTING.md).
- The repo is **Apache-2.0** (`LICENSE`). Note the existing `plugin.json` manifests declare
  `"license": "MIT"` — flag this inconsistency rather than propagating it to new manifests.
