# DataLad Container-Run Reference

## Container registration: `datalad containers-add`

Must be run once per container before any `datalad container-run` calls.

```bash
datalad containers-add <name> \
  --url <image-source> \
  --call-fmt "<runtime-template>"
```

### `--url` — image source

| Source type | Example |
|---|---|
| Local `.sif` file | `--url /path/to/image.sif` |
| Singularity Hub | `--url shub://owner/image:tag` |
| Docker Hub (pull via Singularity) | `--url docker://owner/image:tag` |
| OCI registry (ORAS) | `--url oras://registry/image:tag` |
| Docker Hub (pull via Docker) | `--url docker://owner/image:tag` (with Docker call-fmt) |

### `--call-fmt` — invocation template

The template must contain `{img}` (path to the image) and `{cmd}` (the command to run).
Both placeholders are required.

| Runtime | `--call-fmt` value |
|---|---|
| Singularity | `"singularity exec {img} {cmd}"` |
| Apptainer | `"apptainer exec {img} {cmd}"` |
| Docker | `"docker run --rm -v $(pwd):/work -w /work {img} sh -c '{cmd}'"` |

### `--image` flag

Use `--image` instead of `--url` when the URL resolves to a registry manifest rather
than a direct image file (some OCI registries).

### Example registrations

```bash
# Singularity .sif file
datalad containers-add fmriprep \
  --url /data/containers/fmriprep-23.2.0.sif \
  --call-fmt "singularity exec {img} {cmd}"

# Apptainer from Docker Hub
datalad containers-add freesurfer \
  --url docker://freesurfer/freesurfer:7.4.1 \
  --call-fmt "apptainer exec {img} {cmd}"

# Docker image
datalad containers-add myanalysis \
  --url docker://myorg/myanalysis:latest \
  --call-fmt "docker run --rm -v $(pwd):/work -w /work {img} sh -c '{cmd}'"
```

---

## Listing containers: `datalad containers-list`

```bash
datalad containers-list
```

Shows all registered containers with their names, URLs, and call formats.

---

## Removing a container: `datalad containers-remove`

```bash
datalad containers-remove <name>
```

Deregisters the container from the dataset. Does not delete the image file.

---

## Running inside a container: `datalad container-run`

Inherits all `datalad run` flags and adds `--container-name`.

```bash
datalad container-run \
  --container-name <name> \
  -m "<meaningful message>" \
  [-i <input-path>...] \
  [-o <output-path>...] \
  "<command>"
```

### Key flags

| Flag | Description |
|---|---|
| `--container-name` | Name of a registered container (from `containers-list`) |
| `-m` | Commit message describing the run (required) |
| `-i` | Input file or glob pattern (repeatable) |
| `-o` | Output file or glob pattern (repeatable) |
| `--explicit` | Only stage files listed with `-o`; do not auto-detect outputs |
| `--dry-run` | Show what would be run without executing |
| `--rerun-id` | Re-execute a specific prior run by its ID |

### Provenance stored in the commit

The commit record includes:
- The container name and the image file's annex key (content hash)
- The call format used to invoke the container
- The exact command passed to the container
- Input and output paths with their annex keys

This means `datalad rerun <sha>` will re-fetch the exact image version and re-execute
the same command in the same container.

---

## Reproducing a container-run

```bash
# Re-execute a specific run (re-fetches image if needed)
datalad rerun <commit-sha>

# Re-execute all runs in a branch
datalad rerun --onto HEAD~5 HEAD
```

---

## Common pitfalls

**Missing `{img}` or `{cmd}` in `--call-fmt`**
The container will be invoked with an incomplete command. Always verify both placeholders
are present before running `containers-add`.

**Forgetting `containers-add` before `container-run`**
DataLad will error: "unknown container name". Always check `datalad containers-list`
first.

**Docker bind-mount missing output directory**
If the command writes to a subdirectory that isn't bind-mounted, Docker won't see the
outputs. Ensure `$(pwd)` covers the output paths, or add explicit `-v` mounts.

**Using a local `.sif` without an absolute path**
Relative paths in `--url` can break when the dataset is cloned elsewhere. Prefer
absolute paths or remote URLs so the image can be re-fetched on rerun.

**Large container images and `datalad get`**
The image is annexed by default. On a fresh clone, run `datalad get <image.sif>` before
attempting a rerun, or configure a remote annex to auto-fetch.
