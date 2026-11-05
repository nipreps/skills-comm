# Reference data

Fetched here before grading, from the gated dataset
`neurodeskorg/skills-comm-ground-truth`:

    python benchmark/harness/fetch_reference.py \
        --task structural-brain-extraction --subject <subject>

- `consensus_mask.nii.gz` — binary consensus, native T1w grid
- `consensus_zones.nii.gz` — 0 background, 1 margin, 2 core
- `rubric.json` — written by the fetch, combining this pack's policy with the
  subject's gated calibration

The dataset path and the pinned revision live in
[`benchmark/harness/run_manifest.json`](../../../harness/run_manifest.json), which is what
the fetch reads; they are deliberately not repeated here.

The dataset is gated, which is what keeps the reference out of the plane where the agent
works. Grading reads a token from `HF_TOKEN`; in CI that comes from a repository secret.
Ask the maintainers about access for local use.
