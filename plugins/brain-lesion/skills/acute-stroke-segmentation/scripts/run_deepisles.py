#!/usr/bin/env python3
"""Run the pinned DeepISLES ensemble from a writable job-specific workspace."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dwi", required=True)
    parser.add_argument("--adc", required=True)
    parser.add_argument("--flair")
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    subprocess.run(["nvidia-smi"], check=True, stdout=subprocess.DEVNULL)
    dwi = Path(args.dwi).resolve()
    adc = Path(args.adc).resolve()
    flair = Path(args.flair).resolve() if args.flair else None
    work_dir = Path(args.work_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    if work_dir.exists() and any(work_dir.iterdir()):
        raise SystemExit(f"work directory is not empty: {work_dir}")
    work_dir.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        "/opt/DeepIsles",
        work_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("weights"),
    )

    sys.path.insert(0, "/opt/DeepIsles")
    from src.isles22_ensemble import IslesEnsemble  # type: ignore

    os.chdir(work_dir)
    IslesEnsemble().predict_ensemble(
        ensemble_path=str(work_dir),
        weights_dir="/opt/DeepIsles/weights",
        input_dwi_path=str(dwi),
        input_adc_path=str(adc),
        input_flair_path=str(flair) if flair else None,
        output_path=str(output_dir),
        skull_strip=False,
        fast=False,
        save_team_outputs=False,
        results_mni=False,
        parallelize=True,
    )


if __name__ == "__main__":
    main()
