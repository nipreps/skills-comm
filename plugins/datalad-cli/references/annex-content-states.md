# Git Annex Content States

Understanding annex content states is required before deciding between `datalad drop`
and `datalad remove`.

## The two-layer model

Every annexed file has two independent things that can exist or not exist:

1. **The pointer** (symlink or git-annex metadata) — lives in the git history.
   Deleting the pointer removes the file from the dataset forever.
2. **The content** (actual bytes) — stored in `.git/annex/objects/` or a remote.
   Dropping content frees local disk space while keeping the pointer.

---

## State matrix

| Pointer | Content locally | Outcome |
|---------|----------------|---------|
| exists  | present        | Normal: file is accessible and checked out |
| exists  | absent         | Pointer-only: `ls` shows the symlink; `cat` fails; `datalad get` can restore |
| absent  | n/a            | File is gone from the dataset history entirely |

---

## Operations

### `datalad drop` — free disk space, keep pointer
- Removes local content copy from `.git/annex/objects/`
- The pointer (symlink) remains; the file path still shows up in `git ls-files`
- **Content can be restored later** with `datalad get <path>` IF a remote copy exists
- Fails by default if no other copy of the content exists (safety check)
- Use `--nocheck` to override the safety check (risks data loss if truly no other copy)

```bash
datalad drop <path>
datalad drop --nocheck <path>   # skip remote-availability check
```

### `datalad remove` — delete pointer and content entirely
- Runs `datalad drop` first, then removes the pointer from the git index
- The file disappears from `git ls-files` and from `datalad status`
- **Irreversible** in the local dataset (content may still exist on remotes if pushed)
- Must be followed by `datalad save` to record the removal in history

```bash
datalad remove <path>
datalad save -m "remove <path>"
```

---

## Safety rules

- **Never run `git rm` on an annexed file** — this removes only the pointer without
  dropping content, leaving orphaned annex objects and a corrupt state.
- **Never run `rm` directly on an annexed file** — same corruption risk.
- Before dropping, always check whether a remote copy exists:
  ```bash
  git annex whereis <path>
  ```
  If the output shows only `here`, dropping without `--nocheck` will be blocked.
  Dropping with `--nocheck` when only one copy exists means permanent data loss.

---

### `datalad unlock` — make an annexed file writable for in-place editing

Annexed files are stored as write-protected symlinks. Before editing an annexed file
you must unlock it. Unlike drop/remove, unlock does not change what is in the dataset —
it just temporarily materializes the file as a regular writable file.

- Replaces the symlink with the actual file content
- The file is now writable by normal tools (`vim`, `sed`, scripts)
- **Content must be locally present** — if absent, run `datalad get <path>` first
- After editing, `datalad save` re-annexes the file and records the change

```bash
datalad unlock <path>          # unlock one file
datalad unlock .               # unlock everything in current directory
datalad unlock <p1> <p2>       # unlock multiple files
```

> Tip: `datalad run -o <path>` calls unlock automatically on declared outputs before
> running the command, so you rarely need to call `unlock` manually for pipeline outputs.

---

## When to use each

| Goal | Operation |
|------|-----------|
| Free local disk, file still needed later | `datalad drop` |
| File is no longer needed anywhere | `datalad remove` + `datalad save` |
| Edit an annexed file in place | `datalad unlock` → edit → `datalad save` |
| Retrieve previously dropped content | `datalad get <path>` |
| Check where content copies live | `git annex whereis <path>` |
