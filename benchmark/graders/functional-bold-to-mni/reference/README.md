# Reference data

Fetched here before grading, from the gated dataset
`neurodeskorg/skills-comm-ground-truth`:

    python benchmark/harness/fetch_reference.py --task functional-bold-to-mni

- `template_T1w.nii.gz`
- `template_brain_mask.nii.gz`

The dataset path and the pinned revision live in
[`benchmark/harness/run_manifest.json`](../../harness/run_manifest.json), which is what
the fetch reads; they are deliberately not repeated here.

Access is granted on request. Set `HF_TOKEN` to a token for the account that holds it.
Gating is what keeps the reference out of the plane where the agent works.
