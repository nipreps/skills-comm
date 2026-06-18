---
name: nipoppy-cli
description: >
  Assist with the nipoppy CLI for managing neuroimaging datasets. Use when the user
  asks about nipoppy commands, setting up a nipoppy dataset, organizing DICOM files,
  running BIDS conversion (bidsify), executing processing pipelines (process, fMRIPrep,
  MRIQC), tracking pipeline status (track-processing), extracting imaging-derived
  phenotypes (extract/IDPs), or managing the pipeline catalog (pipeline install/search/
  upload/validate). Also invoke for /nipoppy-cli or when a manifest.tsv or nipoppy
  config.json is present.
argument-hint: [command | question | dataset-path]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob, Grep
---

# Skill: nipoppy-cli

Help users work with the nipoppy CLI for end-to-end neuroimaging dataset management,
from raw DICOMs through BIDS conversion, pipeline execution, and IDP extraction.

## Steps

1. **Identify user context** — determine which workflow stage the user is at:
   - New dataset (no existing directory): direct to `init`
   - Existing dataset: inspect for `config.json` and `manifest.tsv` to confirm it is initialized
   - Command question: identify which command group applies from $ARGUMENTS or user message
   - General workflow question: load `${CLAUDE_PLUGIN_ROOT}/references/workflow-overview.md`

2. **Load relevant reference** — based on the identified context, read the appropriate file:
   - Workflow overview / "what is nipoppy" / "full workflow": `${CLAUDE_PLUGIN_ROOT}/references/workflow-overview.md`
   - `init` or `status`: `${CLAUDE_PLUGIN_ROOT}/references/setup-commands.md`
   - `track-curation` or `reorg`: `${CLAUDE_PLUGIN_ROOT}/references/curation-commands.md`
   - `bidsify`: `${CLAUDE_PLUGIN_ROOT}/references/bids-commands.md`
   - `process`: `${CLAUDE_PLUGIN_ROOT}/references/process-command.md`
   - `track-processing` or `extract`: `${CLAUDE_PLUGIN_ROOT}/references/track-extract-commands.md`
   - `pipeline search`, `pipeline install`, or `pipeline list`: `${CLAUDE_PLUGIN_ROOT}/references/pipeline-catalog-commands.md`
   - `pipeline create`, `pipeline validate`, or `pipeline upload`: `${CLAUDE_PLUGIN_ROOT}/references/pipeline-authoring-commands.md`
   - When uncertain, load `workflow-overview.md` first, then the relevant group reference

3. **Check dataset state** — if a dataset path is provided or discoverable (cwd or $ARGUMENTS):
   - Check for `config.json` (nipoppy dataset marker)
   - Check for `manifest.tsv` (participant/session registry)
   - Check the `manifest.tsv` for a `ses` column — its presence indicates a multi-session
     dataset, which affects BIDS output paths
   - Load `${CLAUDE_PLUGIN_ROOT}/references/setup-commands.md` to determine the expected
     sourcedata path for data readiness checks (do not hardcode the path)
   - Report what is and is not present before giving command advice

4a. **Error handling** — if a pipeline command fails or the user reports an error:
   - Direct the user to check logs under `<dataset>/logs/<pipeline>/<version>/`
   - Report the relevant error lines from the log
   - Re-runs can target specific subjects with `--participant-id` to avoid re-running
     all subjects when only some failed

4. **Provide targeted help** — answer with:
   - Full command syntax for the relevant subcommand(s)
   - Applicable options from the reference, matched to what the user described
   - Example invocations tailored to the user's dataset path and parameters when known
   - Warnings for common pitfalls (missing manifest entries, uninitialized dataset, etc.)

5. **Suggest next step** — after answering, recommend the next logical nipoppy command
   in the standard workflow order: `init` → `track-curation` → `reorg` → `bidsify` → `process` → `track-processing` → `extract`

## Constraints

- Always verify `config.json` and `manifest.tsv` exist before recommending commands that require an initialized dataset (`reorg`, `bidsify`, `process`, `track-processing`, `extract`).
- Always warn that nipoppy pipeline commands (`bidsify`, `process`, `extract`) require Linux and Apptainer; they will not work on macOS or Windows.
- Never run nipoppy commands without `--simulate` or `--dry-run` unless the user explicitly confirms they want live execution. Note that `--simulate` and `--dry-run` availability varies by command — load the relevant reference to confirm which flag applies before suggesting it.
- Never add participants to `manifest.tsv` by hand — instruct the user to edit the file directly or use nipoppy's manifest update workflow.
- When explaining `process` or `extract`, always mention the `--pipeline`, `--pipeline-version`, and `--pipeline-step` options, as omitting them may apply the command to all configured pipelines unexpectedly.
- For HPC workflows, prefer `--hpc slurm` or `--hpc sge` when the cluster type is known
  and supported — nipoppy generates and submits job scripts automatically. Use
  `--write-subcohort` only when the HPC scheduler is unsupported or manual job submission
  control is required; in that case, load `${CLAUDE_PLUGIN_ROOT}/references/process-command.md`
  for the subcohort workflow.
- The `nipoppy pipeline` subgroup manages the pipeline catalog (install/search/upload); it does not run pipelines. Use `process`, `bidsify`, or `extract` to actually run pipelines.
