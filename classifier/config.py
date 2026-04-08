"""Config: .env loading, secret validation, canonical repo paths."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
SPLITS_DIR = DATA_DIR / "splits"
CANDIDATES_DIR = DATA_DIR / "candidates"
LABELING_SHEETS_DIR = REPO_ROOT / "mapping_engine/output/labeling_sheets"

load_dotenv(REPO_ROOT / ".env", override=False)


class MissingSecretError(RuntimeError):
    pass


def require_secrets(keys: list[str]) -> dict[str, str]:
    """Return a dict of key->value for the listed secrets.

    Raises MissingSecretError listing every missing key.
    """
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise MissingSecretError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Copy .env.example to .env and fill them in."
        )
    return {k: os.environ[k] for k in keys}
