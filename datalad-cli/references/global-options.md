# DataLad Global Options Reference

These flags appear **before** the subcommand and apply to every `datalad` command:

```
datalad [global-opts] <subcommand> [subcommand-opts]
```

---

## `-l LEVEL` / `--log-level LEVEL`

Set logging verbosity. Use when a command fails with an opaque error.

```bash
datalad -l debug get myfile.nii.gz
datalad -l info push --to origin
```

Levels (increasing verbosity): `critical`, `error`, `warning` (default), `info`, `debug`

`debug` is the most useful for diagnosis — it prints every git/annex call DataLad makes.
Recommend before escalating any issue to the troubleshooting reference or a bug report.

---

## `--on-failure {ignore,continue,stop}`

Controls what happens when one operation in a batch fails.

| Value | Behaviour |
|-------|-----------|
| `stop` | Abort immediately on first failure (default) |
| `continue` | Log the failure, keep processing remaining items |
| `ignore` | Like `continue`, but the failure does not contribute to a non-zero exit code |

Most important for **recursive operations** (`-r`): a single subdataset failure will
abort the entire tree unless `--on-failure continue` (or `ignore`) is set.

```bash
datalad push --to origin -r --on-failure continue
datalad get -r inputs/ --on-failure continue
datalad update -s origin -r --on-failure continue
```

Use `ignore` only when failures are expected and acceptable (e.g., some siblings offline).
Use `continue` when you want the exit code to still reflect failures.

---

## `-f FORMAT` / `--output-format FORMAT`

Select result rendering. Useful for scripting or parsing output programmatically.

| Format | Output |
|--------|--------|
| `tailored` | Human-readable, command-specific layout (default for most commands) |
| `generic` | Generic human-readable key=value lines |
| `json` | One JSON object per result, one per line (machine-readable) |
| `json_pp` | Pretty-printed JSON (easier to read, harder to stream) |
| `disabled` | Suppress all result output |
| `'<template>'` | Jinja2 template string applied to each result dict |

```bash
datalad -f json status          # parse status results in a script
datalad -f json_pp siblings     # inspect sibling config as structured data
datalad -f disabled save -m "..."  # suppress result noise in CI
```

---

## `-c name=value`

Override a DataLad / git-annex config value for a single invocation without editing
any config file.

```bash
# Force a file into git even if annex.largefiles would annex it
datalad -c annex.largefiles=nothing save myconfig.json -m "add config"

# Treat all .nii.gz files as large for this one save
datalad -c annex.largefiles="*.nii.gz" save -m "add images"
```

Can be repeated for multiple overrides: `-c key1=value1 -c key2=value2`.

To unset a key temporarily, prefix with `:`: `-c :annex.largefiles`.

---

## `-C PATH`

Run as if DataLad was started in `<path>`. Avoids the need to `cd` before running a
command — useful in scripts, CI, or when managing multiple datasets.

```bash
# Save in a subdataset without cd-ing into it
datalad -C /data/myproject/sub-01 save -m "add rawdata"

# Multiple -C flags: each non-absolute path is relative to the preceding one
datalad -C /data -C myproject status
```

---

## `--cmd`

Syntactical disambiguator. Use when a global flag accepts unlimited arguments and you
need to signal where global options end and the subcommand begins.

Rarely needed in practice; most useful in shell scripts where argument lists are
constructed dynamically.

```bash
datalad -c key=value --cmd save -m "message"
```
