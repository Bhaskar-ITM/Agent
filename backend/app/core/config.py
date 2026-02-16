from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JENKINS_BASE_URL: str = "http://jenkins:8080"
    JENKINS_TOKEN: str = "stub-token"

    model_config = {"env_file": ".env"}

settings = Settings()
