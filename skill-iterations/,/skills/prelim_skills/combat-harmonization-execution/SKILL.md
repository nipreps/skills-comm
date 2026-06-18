---
name: combat-harmonization-execution
description: >
  Execute ComBat-family harmonization on a feature matrix. Submit the
  harmonization script to a job scheduler, monitor progress, and validate
  that harmonization completed successfully. Invoke when the user says
  "run harmonization", "execute ComBat", "submit harmonization job",
  "apply batch correction", or when a harmonization script exists and
  needs to be run. Also invoke after generating a harmonization strategy
  to handle the execution step.
---

# ComBat Harmonization Execution

Take a harmonization script and execute it, handling job submission,
monitoring, and validation.

## Workflow

### 1. Locate the harmonization script

Find the most recent analysis script for harmonization:
```bash
ls analysis_*combat_harmonize*.py analysis_*harmoniz*.py 2>/dev/null
```

If none exists, invoke `combat-harmonization-strategy` to generate one first.

### 2. Detect the scheduler

Determine what job scheduler (if any) is available:
```bash
command -v sbatch   # SLURM
command -v qsub     # PBS/Torque
command -v bsub     # LSF
```

### 3. Write submission wrapper

If a scheduler is found, wrap the Python script in a submission script. For SLURM:

```bash
#!/bin/bash
#SBATCH --job-name=combat_harmonize
#SBATCH --output=logs/combat_harmonize_%j.out
#SBATCH --error=logs/combat_harmonize_%j.err
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4

python analysis_<N>_combat_harmonize.py \
    --input-edges <path> \
    --site-metadata <path> \
    --output-dir <path>
```

If no scheduler, run directly but warn the user about resource usage.

### 4. Submit and report

Submit the job and report:
- Job ID
- Command to check status: `squeue -u $USER` or equivalent
- Log file paths for monitoring

### 5. Define validation checks

After submission, write a validation checklist into the logs directory:

```bash
#!/bin/bash
# validation_combat.sh -- run after harmonization completes

EXPECTED_DIR="<output_dir>"

check() {
    if [ -s "$1" ]; then echo "PASS: $1 ($(wc -c < "$1") bytes)"; 
    else echo "FAIL: $1 missing or empty"; fi
}

check "$EXPECTED_DIR/harmonized_edges.npy"
check "$EXPECTED_DIR/input_edges.csv"
check "$EXPECTED_DIR/harmonization_metadata.json"

# Verify shapes match
python3 -c "
import numpy as np
orig = np.load('$EXPECTED_DIR/input_edges.npy', allow_pickle=True)
harm = np.load('$EXPECTED_DIR/harmonized_edges.npy', allow_pickle=True)
assert orig.shape == harm.shape, f'Shape mismatch: {orig.shape} vs {harm.shape}'
print(f'Shapes match: {orig.shape}')
print(f'Before harmonization: mean={orig.mean():.4f}, std={orig.std():.4f}')
print(f'After harmonization:  mean={harm.mean():.4f}, std={harm.std():.4f}')
"
```

### 6. Monitor and report completion

Tell the user to monitor with specific commands:
```
squeue -u $USER
tail -f logs/combat_harmonize_*.out
```

When the job completes, automatically run the validation script and report results.

### 7. Hand off to QC

When validation passes, report:
- Input/output shapes
- Mean/std before/after
- Any NaN values
- File sizes

Then invoke `harmonization-qc` to generate visual quality assessment.

## Constraints

- Never run harmonization interactively on large feature sets — always schedule
- Always validate shapes match between input and output
- Check for NaN values after harmonization (indicates failed EB shrinkage)
- Preserve the original input data — never overwrite it
