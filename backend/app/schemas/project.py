from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ProjectCreate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    name: str
    git_url: str
    branch: str = "main"
    credentials: str
    sonar_key: str
    target_ip: str | None = None
    target_url: str | None = None

class ProjectResponse(ProjectCreate):
    id: str
