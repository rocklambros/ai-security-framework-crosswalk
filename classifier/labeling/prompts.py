from __future__ import annotations
import hashlib
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "config" / "llm_sme_prompts" / "v1"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    autoescape=False,
)


def render_prompt(ctx: dict) -> tuple[str, str]:
    system = _env.get_template("system.j2").render(**ctx)
    user = _env.get_template("user.j2").render(**ctx)
    return system, user


def prompt_sha(system: str, user: str) -> str:
    h = hashlib.sha256()
    h.update(system.encode("utf-8"))
    h.update(b"\x00")
    h.update(user.encode("utf-8"))
    return h.hexdigest()
