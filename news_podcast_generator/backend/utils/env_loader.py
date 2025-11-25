from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def load_backend_env() -> Optional[Path]:
    """
    Load environment variables from the backend `.env` file regardless of the caller's cwd.
    Returns the resolved path to the .env file if found.
    """
    current_path = Path(__file__).resolve()
    for path in current_path.parents:
        candidate = path / ".env"
        if candidate.exists():
            load_dotenv(dotenv_path=candidate, override=False)
            return candidate
    load_dotenv(override=False)
    return None

