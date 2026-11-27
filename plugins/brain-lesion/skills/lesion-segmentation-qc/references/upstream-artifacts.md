# Upstream artifact contract

Use this reference whenever lesion QC lacks a brain mask or a defining modality,
or when an available artifact is not already on the lesion grid.

## Brain mask

1. Reuse a brain mask only when it is already validated and matches the lesion
   mask in both shape and affine.
2. Otherwise, invoke `brain-extraction` with an explicit handoff containing:
   `EXTRACTION_INPUT=<compatible anatomical>`,
   `REFERENCE_GRID=<anatomical on the lesion-output grid>`, and
   `FINAL_MASK=<new brain-mask path>`. These may be the same image, but do not
   leave `REFERENCE_GRID` implicit.
3. Let `brain-extraction` select the method and read its own `references/*.md`.
   Those producer references are the sole source of tool module names,
   invocations, output filenames, resource requests, and known failures.
4. Do not run an extractor directly from lesion QC and do not copy its command
   into this package. In particular, never reconstruct short or long options
   from memory.

After the producer returns, preflight shape and affine against the lesion before
running numeric QC. The consumer flag is exactly:

```bash
python3 <lesion-qc-skill>/scripts/lesion_qc_metrics.py \
  --lesion "<lesion>" --type "<type>" \
  --brain-mask "<producer FINAL_MASK>" \
  <defining-modality flags> --json "<metrics.json>"
```

Do not replace `--brain-mask` with `--mask`, `--brain`, or `--brain_mask`.

If no anatomical image exists on the lesion grid, use a different validated
brain mask only when the images have a declared, valid spatial relationship.
Perform any required nearest-neighbour mask transformation in a retained
numbered SLURM script, validate the result, and record the transform. Otherwise
leave containment UNVERIFIED.

## Defining modality

Use FLAIR for WMH, T1w for chronic stroke, and DWI plus ADC for acute stroke
only when the supplied images match the lesion grid in both shape and affine.
If a registered copy or an already validated transform does not exist, leave
the intensity signature UNVERIFIED. Do not add an unplanned registration merely
to remove an UNVERIFIED rating.

## Why producer ownership matters

QC describes whether an artifact is acceptable; it should not maintain shadow
copies of the commands that create upstream artifacts. Delegation keeps one
tested contract for each tool and ensures a version fingerprint includes both
the consumer and producer skills.

This reference intentionally points to the producer skill instead of copying
its module names or tool commands. The producer's main `SKILL.md` and every
selected `references/*.md` file remain authoritative for creation; this QC
reference owns only the handoff fields, exact consumer flag, and preflight.
