# Reference data

Fetched here before grading, from the gated dataset
`neurodeskorg/skills-comm-ground-truth`:

    python benchmark/harness/fetch_reference.py --task structural-mni-registration

- `template_T1w.nii.gz`
- `template_brain_mask.nii.gz`
- `template_probseg_GM.nii.gz`
- `template_probseg_WM.nii.gz`
- `template_probseg_CSF.nii.gz`

The dataset path and the pinned revision live in
[`benchmark/harness/run_manifest.json`](../../../harness/run_manifest.json), which is what
the fetch reads; they are deliberately not repeated here.

The dataset is gated, which is what keeps the reference out of the plane where the agent
works. Grading reads a token from `HF_TOKEN`; in CI that comes from a repository secret.
Ask the maintainers about access for local use.
