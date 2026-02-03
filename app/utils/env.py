from __future__ import annotations
from dotenv import load_dotenv as dotenv_load_dotenv

def load_dotenv(env_file: str | None) -> None:
    """Load environment variables from a dotenv file if present.

    This is a small helper so the entrypoint can stay focused.
    """

    if not env_file:
        return

    dotenv_load_dotenv(env_file, override=False)
