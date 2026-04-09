"""Deploy the Dash app to HuggingFace Spaces.

Usage:
    python -m app.scripts.deploy_hf_space --dry-run
    python -m app.scripts.deploy_hf_space --repo-id <user/repo>
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ATTR_FILE = _REPO_ROOT / "app" / "deploy" / "THIRD_PARTY_NOTICES.md"
_REPO_ATTR = _REPO_ROOT / "THIRD_PARTY_NOTICES.md"
_LICENSING_REVIEW = _REPO_ROOT / "app" / "deploy" / "LICENSING_REVIEW.md"


def _check_preconditions() -> None:
    if _ATTR_FILE.exists():
        if _REPO_ATTR.exists() and _ATTR_FILE.read_bytes() != _REPO_ATTR.read_bytes():
            sys.exit(
                "DEPLOY ABORTED: app/deploy/THIRD_PARTY_NOTICES.md is stale vs. "
                "repo-root THIRD_PARTY_NOTICES.md. Re-copy before deploying."
            )
    if os.environ.get("ALLOW_WEIGHTS_REDISTRIBUTION") == "1":
        if not _LICENSING_REVIEW.exists():
            sys.exit(
                "DEPLOY ABORTED: ALLOW_WEIGHTS_REDISTRIBUTION=1 requires "
                "app/deploy/LICENSING_REVIEW.md on disk (reviewed sign-off "
                "of CC BY-SA 4.0 ShareAlike obligations on derived weights). "
                "See spec §8 risk row."
            )
        print("WEIGHTS REDISTRIBUTION MODE (gated by LICENSING_REVIEW.md)")
    else:
        print("INFERENCE-ONLY deploy (no raw weights redistributed)")


def main():
    parser = argparse.ArgumentParser(description="Deploy to HuggingFace Spaces")
    parser.add_argument("--repo-id", type=str, default=None, help="HF Space repo ID")
    parser.add_argument("--dry-run", action="store_true", help="Check preconditions only")
    args = parser.parse_args()

    _check_preconditions()

    if args.dry_run:
        print("Dry run complete. Preconditions OK.")
        return

    if not args.repo_id:
        sys.exit("ERROR: --repo-id required for actual deploy")

    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(args.repo_id, repo_type="space", space_sdk="docker", exist_ok=True)
    api.upload_folder(
        folder_path=str(_REPO_ROOT),
        repo_id=args.repo_id,
        repo_type="space",
        ignore_patterns=["*.pyc", "__pycache__", ".git", "*.egg-info"],
    )
    print(f"Deployed to https://huggingface.co/spaces/{args.repo_id}")


if __name__ == "__main__":
    main()
