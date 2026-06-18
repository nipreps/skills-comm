---
name: job-monitor
description: >
  Monitor SLURM/PBS/LSF jobs, tail logs live, detect errors immediately as they
  appear in log output, cancel the job on fatal error so the user can iterate
  fast, and report status. Invoke when the user asks to "check my jobs",
  "monitor", "what's running", "did it finish", "job status", "check logs",
  "is it done", or after any sbatch/qsub submission. Also invoke proactively
  after every job submission — the default behavior is to immediately start
  watching logs for errors.
---

# Job Monitor

Track compute jobs from submission through completion with a focus on **fast
failure detection**. The goal is minimal round-trips: catch errors as soon as
they hit the log, kill the job, and report so the code can be fixed.

## Workflow

### 1. Immediate post-submission check

After every `sbatch` / `qsub`, immediately:

```bash
squeue -u $USER --format="%i %j %T %M %l" 2>/dev/null
```

Wait ~5 seconds for the scheduler to create the log file, then tail the `.err`
and `.out` for the first signs of trouble:

```bash
# Wait for log files to appear
for i in $(seq 1 6); do
    if [ -f "logs/<jobname>_$JOBID.err" ]; then break; fi
    sleep 2
done
```

### 2. Live error scan (primary workflow)

**While the job is RUNNING**, repeatedly scan the error log for Python
tracebacks shell/fatal errors. The moment one appears:

```bash
# Check .err log for tracebacks or fatal errors
grep -c "Traceback\|Error:\|error:\|FATAL\|ModuleNotFoundError\|ImportError\|AttributeError\|NameError\|SyntaxError\|FileNotFoundError" logs/<jobname>_$JOBID.err 2>/dev/null
```

If any match found:
1. **Immediately cancel the job**: `scancel $JOBID`
2. **Read the full traceback** from the `.err` file
3. **Report the exact error to the user** so they can fix and resubmit
4. Show the last few lines of `.out` for context

**Do NOT wait for the scheduler to mark the job as FAILED.** The scheduler may
not notice for minutes. A Python `AttributeError` kills the script instantly —
cancel and report right away.

### 3. When to poll vs when to tail

- **First 30 seconds after submission**: Poll every 3 seconds — most fatal
  errors (imports, syntax, path issues) happen immediately
- **After 30 seconds with no error**: Switch to checking every 10 seconds while
  showing progress from `.out`
- **Once processing visible output appears**: Poll every 15 seconds, show the
  last processed subject/file count

### 4. Health marks

Look for positive signals in stdout while running:
```
"Processing sub-"  → extraction started
"OK"               → subject completed successfully  
"FAIL"             → subject failed but pipeline continued
"DONE"             → all subjects finished
```

Count successes/failures mid-stream:
```bash
grep -c "OK " logs/*.out   # how many succeeded
grep -c "FAIL " logs/*.out  # how many failed (pipeline tolerated)
```

### 5. Determine job state

| State | Meaning | Action |
|-------|---------|--------|
| PENDING/PD | Waiting for resources | Report queue position, retry in 10s |
| RUNNING/R + no stderr errors | Healthy | Show progress counts from stdout |
| RUNNING/R + traceback in stderr | Fatal error | Cancel immediately, report error |
| COMPLETED/CD | Finished | Validate outputs exist |
| FAILED/F/TIMEOUT | Scheduler-detected failure | Read logs, diagnose |

### 6. Reporting format

```
Job 5 (fc_extract): CANCELLED after 12s - FATAL ERROR
  Error: AttributeError: 'NiftiLabelsMasker' object has no attribute 'clone'
  File: analysis_04_fc_extraction.py, line 275

Or for a running healthy job:
Job 6 (fc_extract): RUNNING 45s [3/10 OK, 0 FAIL] -- no errors yet
```

### 7. When to stop monitoring

Stop when one of these happens:
- The job fully completes (`DONE` marker or scheduler COMPLETED)
- A hard error is detected and we cancel
- The user interrupts

## Constraints

- Never assume a specific scheduler — detect and adapt
- Cancel jobs with fatal Python errors immediately — don't let them waste queue time
- Always show the exact error line number and message
- For running jobs, always provide a running count of good vs failed subjects
- Default to aggressive error scanning for the first minute
