# nipoppy-cli

Claude Code skill for the [nipoppy](https://nipoppy.readthedocs.io) neuroimaging
dataset management CLI.

## What it does

Provides Claude with working knowledge of all 8 nipoppy subcommands across the full
dataset lifecycle: `init` → `track-curation` → `reorg` → `bidsify` → `run` → `track`
→ `extract`, plus `status` at any point.

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/nipoppy-cli

# Permanent install
claude plugin install ./plugins/nipoppy-cli
```

## Usage

**Auto-invoked** when the user asks about nipoppy commands, initializing a dataset,
organizing DICOMs, running BIDS conversion, executing fMRIPrep/MRIQC, or extracting IDPs.

**Slash command:** `/nipoppy-cli [command | question | dataset-path]`

## References

| File | Contents |
|------|----------|
| `references/workflow-overview.md` | Full workflow diagram, key files, glossary, platform requirements |
| `references/setup-commands.md` | `init` and `status` — options and examples |
| `references/curation-commands.md` | `track-curation` and `reorg` — options, DICOM checks, curation status schema |
| `references/bids-commands.md` | `bidsify` — dcm2bids, HeuDiConv, BIDScoin options and Boutiques context |
| `references/pipeline-commands.md` | `run`, `track`, `extract` — options, bagel schema, IDP extraction |
