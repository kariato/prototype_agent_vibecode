from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Workspace & State
    WORKSPACE_ROOT_DEFAULT: str = "/Volumes/NVME/Source/prototype_agent_vibecode"
    ALLOWED_WORKSPACE_ROOTS: List[str] = ["/Volumes/NVME/Source/prototype_agent_vibecode", "/tmp"]
    
    ARTIFACTS_DIRNAME: str = ".agent_ide/artifacts"
    PROJECT_STATE_FILENAME: str = "project_state.json"
    
    # Document Paths
    DOCUMENTS_DIRNAME: str = "documents"
    RUN_LOGS_DIRNAME: str = "documents/RUN_LOGS"
    PHASES_DIRNAME: str = "documents/PHASES"
    DECISIONS_DIRNAME: str = "documents/DECISIONS"
    ARCHIVE_DIRNAME: str = "documents/_archive"
    
    # Limits
    MAX_ACTIONS_PER_BUNDLE: int = 3
    MAX_REPAIR_ATTEMPTS: int = 3
    
    # Safety
    DENYLIST_PATH_PREFIXES: List[str] = [
        ".git/",
        ".agent_ide/",
        "/etc/",
        "/usr/",
        "/var/"
    ]
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # "openai", "gemini", "ollama"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: Optional[str] = "https://api.openai.com/v1"
    
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    class Config:
        env_file = ".env"
        case_sensitive = True

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        from .env import load_env
        load_env()
        _settings = Settings()
    return _settings
