from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: Literal["dev", "test", "staging"]
    DATABASE_URL: str
    JENKINS_BASE_URL: str
    JENKINS_TOKEN: str
    STORAGE_PATH: str
    SCAN_TIMEOUT: int
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    DEBUG: bool = False
    MOCK_EXECUTION: bool = False

    model_config = SettingsConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_rules(self):
        if self.ENV == "staging" and self.DEBUG:
            raise ValueError("DEBUG must be false in staging")

        if self.SCAN_TIMEOUT <= 0:
            raise ValueError("SCAN_TIMEOUT must be a positive integer")

        if self.ENV == "test" and not self.MOCK_EXECUTION:
            raise ValueError("MOCK_EXECUTION must be true in test environment")

        return self


settings = Settings()
