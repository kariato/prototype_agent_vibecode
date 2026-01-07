import os
from dotenv import load_dotenv
from pathlib import Path

def load_env():
    """Load environment variables from .env file if it exists."""
    # Look for .env in current working directory or up one level (repo root)
    dotenv_path = Path(".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
    elif Path("..").joinpath(".env").exists():
        load_dotenv(Path("..").joinpath(".env"))
