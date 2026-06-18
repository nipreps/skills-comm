# AGENTS_CONTRIBUTING.md

How an LLM agent should prepare a contribution to skills-comm. This complements the
human-facing [CONTRIBUTING.md](CONTRIBUTING.md) and the git rules in
[AGENTS_GIT.md](AGENTS_GIT.md) — read all three.

## Ground rules

- **Issue first.** Do not author a new skill unless an issue requesting it exists and a
  maintainer has acknowledged it. If asked to create a skill with no issue, propose opening
  one and surface possible overlap with existing skills under `plugins/`.
- **Don't invent capability.** A skill must reflect how the tool actually behaves. Verify
  flags, subcommands, output paths, and version strings against real documentation or a
  real run — never guess. If you can't verify, say so in the PR rather than shipping it.
- **Commit/push only when the human asks.** Branch before committing; never touch `main`
  directly.

## Where things go

- One contribution = one directory under `plugins/<name>/` (lowercase-hyphenated).
- Full plugins carry `.claude-plugin/plugin.json` + `README.md`; bare skill collections
  are also accepted (see CONTRIBUTING.md §2).
- Long reference material goes in the skill's `references/`, not in `SKILL.md`.

## Authoring a SKILL.md

- Frontmatter `name` matches the directory; `description` is the trigger — enumerate the
  phrases and intents that should activate the skill (mirror the style of existing skills
  like `plugins/bcmcpher/brain-extraction/SKILL.md`).
- Body is a terse, numbered, imperative procedure with an explicit **Constraints** section
  for hard rules.
- Honor the target environment (Neurodesk + Lmod + SLURM): discover tools with
  `module spider`, pin versions in `module load`, write a script and submit via `sbatch`
  instead of running heavy tools directly, and capture provenance (DataLad) where relevant.
- Avoid "Claude-isms" — no first-person meta-commentary, no "As an AI", no filler. Write
  for any agent, not just Claude. (`skill-iterations/2_remove_claudedisms/` shows this pass.)

## Self-check before opening the PR

Confirm each of these and report them in the PR body:

- [ ] An acknowledged issue exists; PR links it with `Closes #NN`.
- [ ] Directory is under `plugins/<name>/`; name doesn't collide.
- [ ] `SKILL.md` frontmatter is valid YAML; `name` matches the directory.
- [ ] `description` lists concrete trigger phrases/intents.
- [ ] Every referenced `references/*.md` file exists and resolves.
- [ ] No hardcoded user/session-specific absolute paths; tools are version-pinned.
- [ ] If a plugin: `plugin.json` is valid JSON and lists every skill; `README.md` present.
- [ ] **Test evidence included** — a real end-to-end run (invocation + key output +
      environment/tool versions). This is mandatory; see CONTRIBUTING.md §4.

## PR title and body

**Title** — Conventional Commits (see AGENTS_GIT.md):

```
feat(<contribution>): <what the skill does>
```

**Body** — use this structure:

```
Closes #NN

## What
One-paragraph summary of the skill and the tool/task it operationalizes.

## Trigger
The phrases/intents that activate it (mirrors the frontmatter description).

## Test evidence
Environment + tool versions, the invocation, and the key output/QC artifact
demonstrating an end-to-end run. Trimmed transcript is fine; redact sensitive data.

## Notes
Anything reviewers should know (deviations from the default environment, follow-ups).
```

Keep commits terse and conventional. Squash incidental fixups before requesting review.
