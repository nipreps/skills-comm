---
name: datalad-addurls
description: >
  Auto-invoke when the user wants to populate a DataLad dataset from a list of URLs —
  e.g., bulk-importing files from a manifest (CSV, TSV, or JSON), ingesting data from
  a remote catalog, or creating a dataset from a URL spreadsheet. Trigger on "add files
  from URLs", "bulk import from manifest", "create dataset from URL list", "ingest data
  from CSV", "addurls", "populate dataset from spreadsheet", or /datalad-addurls.
  Do NOT trigger for downloading a single file (use datalad-run with download-url instead).
argument-hint: [manifest-file] [url-column] [filename-column]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-addurls

Bulk-populate a DataLad dataset by reading a URL manifest and adding each file as an
annexed entry with its download URL registered as the annex remote. DataLad will fetch
content on demand with `datalad get`.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or a
   parent:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If no dataset is found, ask the user whether to initialize one first with `/datalad-init`.

2. **Identify the manifest file** — read from `$ARGUMENTS` or conversation context.
   The manifest is a file with one row per file to ingest. Supported formats:
   - **CSV / TSV**: columns delimited by comma or tab
   - **JSON / JSON-Lines**: array of objects or one object per line

   If no manifest is provided, ask the user to specify the file path.

3. **Inspect the manifest** — read the first few lines:
   ```bash
   head -5 <manifest-file>
   ```
   Identify the column (or JSON key) that contains:
   - The **URL** to download from
   - The **local filename** (relative path inside the dataset)

   Ask the user to confirm or correct the column names if ambiguous.

4. **Gather parameters** — confirm:
   - `--url-format` (or positional URL column): the column/key holding the URL
   - `--filename-format` (or positional filename column): the column/key for the local path
   - `--jobs N`: parallel downloads (default 1; suggest 4–8 for large manifests)
   - `-m`: commit message for the resulting dataset commit (required; the auto-generated
     message is unhelpful — always ask the user for a meaningful message)
   - Whether to `--ifexists skip` (skip already-present files) or `overwrite`
   - `--missing-values`: how to handle optional URL fields that are absent in some rows
     (e.g., `--missing-values skip` to skip rows with missing URLs)

5. **Construct and show the command**:

   For CSV/TSV:
   ```bash
   datalad addurls \
     -m "<message>" \
     [--jobs <N>] \
     [--ifexists skip] \
     <manifest-file> \
     '<url-column>' \
     '<filename-column>'
   ```

   For JSON (keys as format strings):
   ```bash
   datalad addurls \
     -m "<message>" \
     --url-format '{url}' \
     --filename-format '{name}' \
     --jobs 4 \
     <manifest-file>.json \
     '{url}' \
     '{name}'
   ```

   Display the full command and ask: > "Ready to execute? (yes / edit)"

6. **Execute and report**:
   - On **success**: report the number of files added, the commit hash created, and that
     content is pointer-only (not yet downloaded) — run `datalad get .` to fetch everything.
   - On **failure**: show the error. Common causes: malformed URLs in manifest, wrong
     column names, network errors. Suggest checking the manifest format.

7. **Post-ingestion suggestions**:
   - To download all content immediately: `datalad get .`
   - To download in parallel: `datalad get -J 8 .`
   - To verify: `datalad status` and `git annex whereis <path>`

## Constraints

- Always inspect the manifest before building the command — never guess column names.
- Always show the full `datalad addurls` command before executing.
- Always require a meaningful `-m` message.
- Warn the user that `addurls` registers URLs as annex remotes but does **not** download
  content by default — files will be pointer-only until `datalad get` is run.
- For large manifests (>100 files), recommend `--jobs 4` or higher and note that the
  initial run creates the commit immediately; downloading happens separately.
- Never edit the manifest file — only read it to determine column names.
