# skills-comm

**A community collection of neuroimaging skills for LLM coding agents.**

`skills-comm` gathers [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
that teach LLM agents (Claude Code and other agents that read `SKILL.md`/`AGENTS.md`)
how to drive real neuroimaging tools **correctly and reproducibly**. Instead of letting
an agent improvise commands for FSL, ANTs, FreeSurfer, DataLad, nipoppy, or a SLURM
cluster, a skill encodes the operational knowledge — the right flags, the safe order of
operations, the quality-control checks, and the reproducibility guardrails — so the work
is repeatable across people and machines.

The goal is **operationalization**: turn "how an expert actually runs this tool" into a
package an agent can load on demand.

## Who this is for

- **Method developers & tool authors** who want their software used the way it was meant
  to be used, even when an LLM is at the keyboard.
- **Neuroimaging researchers** who want a coding agent that follows community
  best-practice (BIDS, YODA/DataLad provenance, explicit tool versioning) by default.
- **Contributors** who want to share a reproducible recipe as a reusable skill.

## What's in here

Each contribution lives under [`plugins/`](plugins/) as its own directory. A contribution
is either a full **Claude Code plugin** (with a `.claude-plugin/plugin.json` manifest) or a
**bare skill collection** (one or more `SKILL.md` directories). Current contributions:

| Plugin | What it operationalizes |
|---|---|
| [`plugins/datalad-cli`](plugins/datalad-cli) | DataLad / git-annex provenance and YODA-compliant analysis datasets |
| [`plugins/nipoppy-cli`](plugins/nipoppy-cli) | The `nipoppy` dataset-management lifecycle (curation → BIDS → process → extract) |
| [`plugins/bcmcpher`](plugins/bcmcpher) | Brain extraction (skull stripping) and its quality control |
| [`plugins/kodibaga`](plugins/kodibaga) | SLURM/PBS/LSF job monitoring and harmonization workflows |

[`skill-iterations/`](skill-iterations/) is a **teaching example**: the same
brain-extraction skill captured at six successive stages of refinement, showing how a raw
draft is hardened into a reliable skill (fixing YAML, removing "Claude-isms", generalizing
across tools, improving QC). Read it to see what "good" looks like before you write your own.

## Skill anatomy

A skill is a directory containing a `SKILL.md` with YAML frontmatter and optional
`references/` files that the agent loads only when needed:

```
my-skill/
├── SKILL.md            # frontmatter (name, description) + the procedure
└── references/         # detailed, load-on-demand material (tool flags, QC criteria, ...)
```

The `description` field is the trigger: it should list the phrases and intents that
should activate the skill. The body is a terse, imperative procedure — not a tutorial.

## Using these skills

Install a plugin into Claude Code (session-only for testing, or permanently):

```bash
# Try it for one session
claude --plugin-dir ./plugins/datalad-cli

# Install permanently
claude plugin install ./plugins/datalad-cli
```

See each plugin's own `README.md` for its skills and slash commands.

## Contributing

We welcome new skills. **Open an issue first** to propose the skill, then send a PR.
Read [CONTRIBUTING.md](CONTRIBUTING.md) for the full procedure (issue → structure →
manual test with evidence → review). Agents contributing on a human's behalf should also
read [AGENTS_CONTRIBUTING.md](AGENTS_CONTRIBUTING.md) and [AGENTS_GIT.md](AGENTS_GIT.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE). By contributing you agree your contribution
is licensed under the same terms.
