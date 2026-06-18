# Nipoppy Pipeline Catalog Commands: `search`, `install`, `list`

These commands manage pipelines within a dataset. Use them to discover pipelines
available on Zenodo, install them locally, and review what is installed.

## `nipoppy pipeline search`

Search Zenodo for pipelines shared by the community.

### Synopsis

```bash
nipoppy pipeline search [OPTIONS] [QUERY]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `QUERY` | Optional search string (e.g., `fmriprep`, `mriqc`). Omit to list all. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--size N` / `-s N` / `-n N` | 10 | Number of results to show. |
| `--community` | off | Restrict results to the official Nipoppy Zenodo community only. |
| `--password-file FILE` | — | Path to a file containing a Zenodo access token (for private records). |
| `--sandbox` | off | Use the Zenodo sandbox API (for testing). |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print actions without executing. |

### Example invocations

```bash
# List all community pipelines
nipoppy pipeline search --community

# Search for fmriprep pipelines
nipoppy pipeline search fmriprep

# Show top 20 results
nipoppy pipeline search mriqc --size 20
```

---

## `nipoppy pipeline install`

Install a pipeline into a dataset. The source can be a local directory path or a
Zenodo record ID (e.g., `1234567`).

### Synopsis

```bash
nipoppy pipeline install [OPTIONS] SOURCE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SOURCE` | A local path to a pipeline config directory, or a Zenodo record ID string. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--password-file FILE` | — | Zenodo access token file (for private or sandbox records). |
| `--sandbox` | off | Use the Zenodo sandbox API. |
| `--force` / `--overwrite` / `-f` | off | Overwrite the pipeline directory if it already exists. |
| `--assume-yes` / `--yes` / `-y` | off | Answer yes to all confirmation prompts. |
| `--layout FILE` | default | Custom layout specification file. |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print actions without executing. |

### Example invocations

```bash
# Install from a local directory
nipoppy pipeline install ./my-fmriprep-config --dataset /data/my-study

# Install from Zenodo by record ID
nipoppy pipeline install 1234567 --dataset /data/my-study

# Install from Zenodo, overwriting any existing version
nipoppy pipeline install 1234567 --dataset /data/my-study --force

# Non-interactive install (CI/automation)
nipoppy pipeline install 1234567 --dataset /data/my-study --assume-yes
```

---

## `nipoppy pipeline list`

List all pipeline config directories currently installed in a dataset.

### Synopsis

```bash
nipoppy pipeline list [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--layout FILE` | default | Custom layout specification file. |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print actions without executing. |

### Example invocations

```bash
# List pipelines in the current dataset
nipoppy pipeline list

# List pipelines in a specific dataset
nipoppy pipeline list --dataset /data/my-study
```
