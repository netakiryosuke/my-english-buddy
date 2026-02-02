from __future__ import annotations


def load_dotenv(env_file: str | None) -> None:
    """Load environment variables from a dotenv file if present.

    This is a small helper so the entrypoint can stay focused.
    """

    if not env_file:
        return

    try:
        from dotenv import load_dotenv as dotenv_load_dotenv
    except (ImportError, ModuleNotFoundError):
        # Optional at runtime; dependency is included in pyproject.toml.
        return

    dotenv_load_dotenv(env_file, override=False)
