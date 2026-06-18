---
name: datalad-credentials
description: >
  Auto-invoke when the user needs to set up credentials for a DataLad remote, gets an
  authentication error pushing to GitHub/OSF/S3/Figshare, or asks how to store tokens
  for DataLad siblings. Trigger on "set up credentials", "configure token", "authentication
  error", "credential error", "how do I authenticate", "store my GitHub token for DataLad",
  "OSF token", "S3 credentials", or /datalad-credentials. Do NOT trigger for general
  SSH key setup or non-DataLad credential management.
argument-hint: [credential-name]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-credentials

Configure credentials that DataLad needs to authenticate with remote storage (GitHub,
OSF, S3, WebDAV, HTTP). Credentials are stored in the system keyring and retrieved
automatically during `datalad push`, `datalad get`, and sibling operations.

## Steps

### Identifying the needed credential

1. **Determine the remote type** from the error or user's description:
   - GitHub / GitLab / Gitea → personal access token (PAT) or SSH key
   - OSF (Open Science Framework) → OSF token
   - S3 / AWS → access key + secret key
   - WebDAV / HTTP → username + password
   - Figshare → API token
   - GIN (G-Node Infrastructure) → SSH key pair (no PAT equivalent for annex operations).
     Generate a key with `ssh-keygen` and add the public key to your GIN account at
     `gin.g-node.org` → Settings → SSH Keys. DataLad uses the SSH key automatically —
     no `datalad credentials set` step is needed for GIN.

2. **Check existing credentials** — list what is already stored:
   ```bash
   datalad credentials
   ```

### Storing a credential

3. **Set a credential by name**:
   ```bash
   datalad credentials set <credential-name>
   ```
   DataLad prompts interactively for the secret. Use a descriptive name, e.g.:
   - `github-pat` for a GitHub personal access token
   - `osf-token` for an OSF token
   - `s3-mybucket` for S3 credentials

   For S3 credentials (requires both key and secret):
   ```bash
   datalad credentials set s3-mybucket --field key_id=<access-key-id>
   # DataLad then prompts for the secret key
   ```

4. **Environment variable alternative** — for CI/CD or temporary use, credentials can
   be passed via environment variables without storing in the keyring:
   ```bash
   DATALAD_CREDENTIAL_<NAME>_TOKEN=<value> datalad push --to <sibling>
   ```
   The variable name is uppercase with underscores. For S3:
   ```bash
   DATALAD_CREDENTIAL_S3_MYBUCKET_KEY_ID=<id>
   DATALAD_CREDENTIAL_S3_MYBUCKET_SECRET_ID=<secret>
   ```

### Verifying and removing credentials

5. **Get/verify a stored credential**:
   ```bash
   datalad credentials get <credential-name>
   ```

6. **Remove a credential**:
   ```bash
   datalad credentials remove <credential-name>
   ```

### Linking credentials to a sibling

After storing a credential, tell the sibling to use it:
```bash
datalad siblings configure --name <sibling-name> --set-property credential <credential-name>
```

## Common authentication errors and fixes

| Error | Likely cause | Fix |
|-------|--------------|-----|
| `403 Forbidden` on push | PAT lacks write permission | Regenerate token with `repo` scope |
| `Authentication failed` | Wrong credential name | Run `datalad credentials` to check stored names |
| `credential not found` | Credential not set | Run `datalad credentials set <name>` |
| `git-annex: S3 error` | Missing S3 credential | Set both `key_id` and secret via `datalad credentials set` |

## Constraints

- Never display a credential secret in plain text — use `datalad credentials get` only
  to verify a credential exists, not to echo the secret to the terminal.
- Always use `datalad credentials set` for interactive storage — never write secrets
  to `.datalad/config`, `.git/config`, or any tracked file.
- For GitHub siblings, prefer HTTPS PAT over SSH if the user has not set up SSH keys —
  it is simpler to configure with `datalad credentials set`.
- Always check `datalad credentials` (list) before asking the user to set credentials —
  the credential may already exist under a different name.
- For rclone-based special remotes (`git-annex-remote-rclone`), credentials are managed
  via `rclone config`, not `datalad credentials` — these are entirely separate systems.
  Direct the user to `rclone config` for rclone remote authentication.
