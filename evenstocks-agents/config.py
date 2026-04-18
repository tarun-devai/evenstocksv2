import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    DEEP_MODEL: str = os.getenv("DEEP_MODEL", "claude-sonnet-4-6")
    QUICK_MODEL: str = os.getenv("QUICK_MODEL", "claude-haiku-4-5-20251001")

    DB_HOST: str = os.getenv("DB_HOST", "mysql")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "example")
    DB_NAME: str = os.getenv("DB_NAME", "evenstocks_db")

    MAX_DEBATE_ROUNDS: int = int(os.getenv("MAX_DEBATE_ROUNDS", "1"))
    ANALYSIS_TIMEOUT_SEC: int = int(os.getenv("ANALYSIS_TIMEOUT_SEC", "120"))


settings = Settings()
