---
name: datalad-export
description: >
  Auto-invoke when the user wants to export a DataLad dataset as an archive file (TAR,
  ZIP) for sharing or backup, or publish a dataset directly to Figshare. Trigger on
  "export dataset", "create archive", "zip the dataset", "tar the dataset", "publish
  to Figshare", "export to Figshare", "make a shareable archive", or /datalad-export.
  Do NOT trigger for pushing to a sibling (use datalad-push) or creating a new remote
  (use datalad-siblings).
argument-hint: [archive|figshare] [--filename path.tar.gz]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-export

Export a DataLad dataset for archiving or open publishing. Two workflows are supported:
local archive creation (TAR/ZIP) and direct Figshare publication.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If no dataset is found, inform the user and stop.

2. **Determine export target** — from `$ARGUMENTS` or conversation context:
   - **archive**: produce a local TAR or ZIP file
   - **figshare**: publish to Figshare (requires `datalad-deprecated` or
     `datalad-mihextras` extension; check availability first)

3. **Execute based on target**:

   ### export-archive (local TAR/ZIP)

   Gather:
   - Output filename (e.g., `dataset-v1.tar.gz`)
   - Archive format: `tar` (default) or `zip`
   - Whether to include all annexed content (`--missing-content error|ignore|annex`)

   ```bash
   datalad export-archive \
     --filename <output-file.tar.gz> \
     [--missing-content ignore]
   ```

   - The archive contains the full git history plus all locally present annexed content.
   - Files whose content is not locally present (pointer-only) are handled per
     `--missing-content`:
     - `error` (default): fail if any content is missing
     - `ignore`: skip missing content (archive will be incomplete)
     - `annex`: include only the pointer (no content bytes)
   - Before exporting, suggest running `datalad get .` to ensure all content is local.

   Show the full command and confirm before executing. After completion, report the
   archive path and size.

   ### export-to-figshare

   Requires a Figshare personal access token. Check for the extension:
   ```bash
   python -c "import datalad_mihextras" 2>/dev/null || echo "extension not installed"
   ```

   Gather:
   - Figshare article ID (create one at figshare.com first if needed)
   - Which files to publish (default: all annexed files)

   ```bash
   datalad export-to-figshare \
     --article <article-id>
   ```

   The token is read from the `FIGSHARE_TOKEN` environment variable or the DataLad
   credential store. If not set, prompt the user to configure it:
   ```bash
   datalad credentials set figshare token=<token>
   ```

   Warn the user that Figshare has a 20 GB per-file limit and that publishing is not
   easily reversible (items can be made private but not fully deleted via the API).

4. **Post-export** — for archives, suggest verifying integrity:
   ```bash
   tar -tzf <output-file.tar.gz> | head -20
   ```

## Constraints

- Always show the full command before executing.
- For `export-archive`: always check whether annexed content is locally present before
  exporting — an incomplete archive may be misleading. Suggest `datalad get .` first.
- For `export-to-figshare`: confirm the article ID with the user before uploading —
  uploads to the wrong article cannot be undone easily.
- Never recommend `export-archive` as a substitute for a proper sibling/remote — archives
  are one-time snapshots, not live remotes that can be pushed to or cloned from.
