import json
import tempfile
import unittest
from pathlib import Path

from benchmark.harness import grade_wrapper


class GradeWrapperTests(unittest.TestCase):
    def test_missing_required_secondary_output_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness = root / "harness"
            pack = root / "graders" / "registration"
            submission = root / "run"
            harness.mkdir()
            pack.mkdir(parents=True)
            (pack / "rubric.json").write_text("{}")

            scorer = pack / "score.py"
            scorer.write_text(
                "import argparse\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('--warped', required=True)\n"
                "p.add_argument('--dseg', required=True)\n"
                "p.add_argument('--pack', required=True)\n"
                "p.add_argument('--json', required=True)\n"
                "p.parse_args()\n"
            )

            manifest = {
                "defaults": {"submission_output_path": "submissions/{task_id}/output.nii.gz"},
                "tasks": {
                    "registration": {
                        "pack_dir": "graders/registration",
                        "scorer": "graders/registration/score.py",
                        "pred_flag": "--warped",
                        "detail_kind": "registration",
                        "required_inputs": {
                            "--dseg": "submissions/{task_id}/dseg.nii.gz"
                        },
                    }
                },
            }
            manifest_path = harness / "run_manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            output = submission / "submissions" / "registration" / "output.nii.gz"
            output.parent.mkdir(parents=True)
            output.touch()

            result = grade_wrapper.grade("registration", submission, manifest_path)

            self.assertEqual(result["verdict"], "invalid")
            self.assertEqual(result["gate_failures"], ["missing_required_output:dseg.nii.gz"])

    def test_per_subject_task_is_graded_at_the_subject_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness = root / "harness"
            pack = root / "graders" / "bet"
            submission = root / "run"
            harness.mkdir()
            (pack / "rubrics").mkdir(parents=True)
            (pack / "rubrics" / "policy.json").write_text("{}")

            # A scorer that reports back which mask it was given.
            scorer = pack / "score.py"
            scorer.write_text(
                "import argparse, json\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('--mask', required=True)\n"
                "p.add_argument('--stripped')\n"
                "p.add_argument('--pack', required=True)\n"
                "p.add_argument('--json', required=True)\n"
                "a = p.parse_args()\n"
                "json.dump({'verdict': 'acceptable', 'quality': 80.0, 'gate_failures': [],\n"
                "           'metrics': {'dice': 0.9}, 'mask': a.mask}, open(a.json, 'w'))\n"
            )

            manifest = {
                "defaults": {
                    "submission_output_path": "submissions/{task_id}/output.nii.gz",
                    "submission_path": "submissions/{task_id}/{subject}/output.nii.gz",
                },
                "tasks": {
                    "bet": {
                        "pack_dir": "graders/bet",
                        "scorer": "graders/bet/score.py",
                        "pred_flag": "--mask",
                        "detail_kind": "binary",
                        "optional_inputs": {
                            "--stripped": "submissions/{task_id}/{subject}/stripped.nii.gz"
                        },
                        "per_subject": True,
                        "subjects": ["sub-01", "sub-02"],
                    },
                    "single": {
                        "pack_dir": "graders/bet",
                        "scorer": "graders/bet/score.py",
                        "pred_flag": "--mask",
                        "detail_kind": "binary",
                    },
                },
            }
            manifest_path = harness / "run_manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            output = submission / "submissions" / "bet" / "sub-01" / "output.nii.gz"
            output.parent.mkdir(parents=True)
            output.touch()

            result = grade_wrapper.grade("bet", submission, manifest_path, subject="sub-01")

            self.assertEqual(result["verdict"], "acceptable")
            self.assertEqual(result["subject"], "sub-01")
            self.assertEqual(Path(result["raw"]["mask"]), output)

            # The other subject's output is not there: a missing output, not a crash.
            other = grade_wrapper.grade("bet", submission, manifest_path, subject="sub-02")
            self.assertEqual(other["gate_failures"], ["missing_output"])
            self.assertEqual(other["subject"], "sub-02")

            # The id and the task have to agree.
            with self.assertRaises(SystemExit):
                grade_wrapper.grade("bet", submission, manifest_path)
            with self.assertRaises(SystemExit):
                grade_wrapper.grade("bet", submission, manifest_path, subject="sub-09")
            with self.assertRaises(SystemExit):
                grade_wrapper.grade("single", submission, manifest_path, subject="sub-01")


if __name__ == "__main__":
    unittest.main()
