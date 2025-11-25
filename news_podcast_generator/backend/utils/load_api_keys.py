import os

from utils.env_loader import load_backend_env


def load_api_key(key_name: str = "OPENAI_API_KEY"):
    load_backend_env()
    return os.environ.get(key_name)
