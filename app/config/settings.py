"""
app/config/settings.py

Defines the global configuration settings for the Agent IDE.
Uses pydantic-settings to load values from environment variables and defaults.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """
    Global application settings schema.
    
    Attributes:
        WORKSPACE_ROOT_DEFAULT: Default path to the workspace if not specified elsewhere.
        ALLOWED_WORKSPACE_ROOTS: Whitelist of allowed workspace roots for security.
        ARTIFACTS_DIRNAME: Directory for internal agent artifacts.
        PROJECT_STATE_FILENAME: Filename for the JSON project state.
        
        DOCUMENTS_DIRNAME: Root directory for project documents.
        RUN_LOGS_DIRNAME: Directory for execution run logs.
        PHASES_DIRNAME: Directory for phase documentation.
        DECISIONS_DIRNAME: Directory for ADRs and decision records.
        ARCHIVE_DIRNAME: Directory for archived versions of documents.
        
        MAX_ACTIONS_PER_BUNDLE: Maximum number of DocOps actions allowed in one proposal.
        MAX_REPAIR_ATTEMPTS: Maximum number of times the agent can try to self-repair a failed step.
        
        DENYLIST_PATH_PREFIXES: List of path prefixes that the agent is strictly forbidden from touching.
        
        LLM_PROVIDER: selected LLM backend ("openai", "gemini", "ollama").
        OPENAI_API_KEY: API key for OpenAI.
        OPENAI_MODEL: Model identifier for OpenAI.
        OPENAI_BASE_URL: Base URL for OpenAI API (optional).
        
        GEMINI_API_KEY: API key for Google Gemini.
        GEMINI_MODEL: Model identifier for Gemini.
        
        OLLAMA_BASE_URL: Base URL for Ollama local inference.
        OLLAMA_MODEL: Model identifier for Ollama.
    """
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
    """
    Retrieves the singleton Settings instance.
    Loads environment variables if not already initialized.
    
    Returns:
        Settings: The global application settings object.
    """
    global _settings
    if _settings is None:
        from .env import load_env
        load_env()
        _settings = Settings()
    return _settings
