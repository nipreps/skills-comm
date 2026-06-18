---
name: datalad-fsck
description: >
  Auto-invoke when the user wants to check annex integrity, verify dataset content,
  check for missing or corrupt files, or recover from suspected data corruption.
  Trigger on "check annex integrity", "verify dataset content", "annex fsck",
  "are my files corrupt", "check for missing content", "fsck", "data integrity check",
  or /datalad-fsck. Do NOT trigger for general DataLad status checks or `datalad status`.
argument-hint: [--fast] [path]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-fsck

Check the integrity of annexed file content in a DataLad dataset using `git annex fsck`.
Identifies missing, corrupt, or unreachable content and guides recovery.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or a
   parent:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If no dataset is found, inform the user and stop.

2. **Determine scope** — ask the user:
   - **Fast check** (`--fast`): verifies file sizes and presence only. Quick, recommended
     for routine checks or large datasets. Does **not** verify checksums.
   - **Full check** (no flag): verifies checksums against stored hashes. Thorough but can
     take a very long time on large datasets. Only recommend if corruption is suspected or
     a transfer completed unexpectedly.
   - **Path-scoped check**: optionally limit to a specific file or directory by passing
     the path as an argument.

   Warn the user: a full fsck on a large dataset can take a very long time. Recommend
   `--fast` first unless there is specific reason to suspect checksum-level corruption.

3. **Construct and show command** — display before executing:
   ```bash
   git annex fsck [--fast] [<path>]
   ```
   Ask: **"Ready to run?"**

4. **Execute and interpret output** — run the command and summarize results:
   - **OK**: file is present and (for full check) checksum matches — no action needed
   - **corrupt**: checksum mismatch — file content is damaged
   - **missing**: file is not present locally

   Report counts of OK / corrupt / missing files.

5. **Suggest recovery based on findings**:
   - **Missing content**: run `datalad get <path>` to re-fetch from a known remote
   - **Corrupt content**: drop the corrupt copy with `datalad drop --nocheck <path>`,
     then re-fetch with `datalad get <path>`
   - **Unrecoverable** (no remote has the content): inform the user the content is lost
     and cannot be recovered automatically — escalate to manual investigation

## Constraints

- Always show the full `git annex fsck` command before executing.
- Always warn that a full fsck (without `--fast`) can take a very long time on large
  datasets before starting.
- Never attempt to auto-repair corrupt files without confirming recovery steps with the
  user first.
- Load `${CLAUDE_PLUGIN_ROOT}/../references/troubleshooting.md` when the user needs
  guidance on recovering from corrupt or missing content beyond simple `datalad get`.
